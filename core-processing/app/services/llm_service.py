"""
LLM Service for Hugging Face model loading and inference.

Handles model loading, GPU memory management, and text generation.
"""

import asyncio
import gc
import os
import sys
import time
from pathlib import Path
from typing import Any, Dict, List, Optional

import structlog
import torch
from transformers import (
    AutoModelForCausalLM,
    AutoTokenizer,
    BitsAndBytesConfig,
    StoppingCriteria,
    StoppingCriteriaList,
)

from app.config import settings
from app.models.llm_models import InferenceConfig, ModelInfo

logger = structlog.get_logger(__name__)


class StopOnTokens(StoppingCriteria):
    """Custom stopping criteria for generation."""

    def __init__(self, stop_token_ids: List[List[int]]):
        self.stop_token_ids = stop_token_ids

    def __call__(
        self, input_ids: torch.LongTensor, scores: torch.FloatTensor, **kwargs
    ) -> bool:
        for stop_ids in self.stop_token_ids:
            if len(input_ids[0]) >= len(stop_ids):
                if input_ids[0][-len(stop_ids):].tolist() == stop_ids:
                    return True
        return False


class LLMService:
    """
    Service for loading and running inference with Hugging Face LLMs.

    Supports:
    - Model loading from Hugging Face Hub
    - GPU and CPU inference
    - Quantization (8-bit, 4-bit)
    - Async inference
    - GPU memory management
    """

    def __init__(self):
        self.model = None
        self.tokenizer = None
        self.device = None
        self.is_loaded = False
        self.model_info: Optional[ModelInfo] = None
        self._lock = asyncio.Lock()

    async def load_model(
        self,
        model_name: Optional[str] = None,
        force_reload: bool = False
    ) -> ModelInfo:
        """
        Load the LLM model from Hugging Face.

        Args:
            model_name: Model name/path (uses config default if not provided)
            force_reload: Force reload even if already loaded

        Returns:
            ModelInfo with model details
        """
        async with self._lock:
            if self.is_loaded and not force_reload:
                logger.info("Model already loaded, skipping")
                return self.model_info

            model_name = model_name or settings.MODEL_NAME
            logger.info("Loading LLM model", model_name=model_name)

            start_time = time.time()

            try:
                # Unload existing model if any
                if self.model is not None:
                    await self.unload_model()

                # Determine device
                if settings.USE_GPU and torch.cuda.is_available():
                    self.device = "cuda"
                    logger.info(
                        "Using GPU",
                        device=torch.cuda.get_device_name(0),
                        memory_total=f"{torch.cuda.get_device_properties(0).total_memory / 1024**3:.1f}GB"
                    )
                else:
                    self.device = "cpu"
                    logger.info("Using CPU")

                # Ensure cache directory exists (cross-platform)
                cache_dir = Path(settings.MODEL_CACHE_DIR)
                cache_dir.mkdir(parents=True, exist_ok=True)
                cache_dir_str = str(cache_dir)

                # Load tokenizer
                self.tokenizer = await asyncio.to_thread(
                    AutoTokenizer.from_pretrained,
                    model_name,
                    trust_remote_code=True,
                    token=settings.HF_API_TOKEN,
                    cache_dir=cache_dir_str
                )

                if self.tokenizer.pad_token is None:
                    self.tokenizer.pad_token = self.tokenizer.eos_token

                # Configure quantization if needed
                quantization_config = None
                if settings.LOAD_IN_4BIT:
                    quantization_config = BitsAndBytesConfig(
                        load_in_4bit=True,
                        bnb_4bit_compute_dtype=torch.float16,
                        bnb_4bit_use_double_quant=True,
                        bnb_4bit_quant_type="nf4"
                    )
                elif settings.LOAD_IN_8BIT:
                    quantization_config = BitsAndBytesConfig(
                        load_in_8bit=True
                    )

                # Determine torch dtype
                torch_dtype = getattr(torch, settings.TORCH_DTYPE, torch.float16)

                # Load model
                model_kwargs = {
                    "trust_remote_code": True,
                    "token": settings.HF_API_TOKEN,
                    "cache_dir": cache_dir_str,
                    "torch_dtype": torch_dtype,
                }

                if self.device == "cuda":
                    model_kwargs["device_map"] = settings.DEVICE_MAP
                    if quantization_config:
                        model_kwargs["quantization_config"] = quantization_config
                    if settings.MAX_GPU_MEMORY_MB:
                        model_kwargs["max_memory"] = {
                            0: f"{settings.MAX_GPU_MEMORY_MB}MB"
                        }

                self.model = await asyncio.to_thread(
                    AutoModelForCausalLM.from_pretrained,
                    model_name,
                    **model_kwargs
                )

                if self.device == "cpu":
                    self.model = self.model.to(self.device)

                self.model.eval()
                self.is_loaded = True

                load_time = time.time() - start_time

                # Get memory usage
                memory_usage = None
                if self.device == "cuda":
                    memory_usage = torch.cuda.memory_allocated() / 1024 / 1024

                # Create model info
                self.model_info = ModelInfo(
                    name=model_name,
                    version=getattr(self.model.config, "model_version", None),
                    parameters=sum(p.numel() for p in self.model.parameters()),
                    device=self.device,
                    dtype=str(torch_dtype),
                    max_sequence_length=getattr(
                        self.model.config,
                        "max_position_embeddings",
                        settings.MAX_SEQUENCE_LENGTH
                    ),
                    loaded_at=time.time(),
                    memory_usage_mb=memory_usage
                )

                logger.info(
                    "Model loaded successfully",
                    model_name=model_name,
                    load_time_seconds=round(load_time, 2),
                    parameters=self.model_info.parameters,
                    memory_mb=memory_usage
                )

                return self.model_info

            except Exception as e:
                logger.error(
                    "Failed to load model",
                    model_name=model_name,
                    error=str(e)
                )
                self.is_loaded = False
                raise

    async def unload_model(self):
        """Unload the model and free memory."""
        async with self._lock:
            if self.model is not None:
                del self.model
                self.model = None

            if self.tokenizer is not None:
                del self.tokenizer
                self.tokenizer = None

            self.is_loaded = False
            self.model_info = None

            # Clear GPU cache
            if torch.cuda.is_available():
                torch.cuda.empty_cache()

            gc.collect()
            logger.info("Model unloaded and memory cleared")

    async def generate(
        self,
        prompt: str,
        config: Optional[InferenceConfig] = None,
        stop_sequences: Optional[List[str]] = None
    ) -> Dict[str, Any]:
        """
        Generate text using the loaded model.

        Args:
            prompt: Input prompt for generation
            config: Inference configuration
            stop_sequences: Sequences to stop generation

        Returns:
            Dict with generated text, tokens used, and generation time
        """
        if not self.is_loaded:
            raise RuntimeError("Model not loaded. Call load_model() first.")

        config = config or InferenceConfig()
        start_time = time.time()

        try:
            # Check GPU memory and clear cache if needed
            await self._manage_gpu_memory()

            # Tokenize input
            inputs = self.tokenizer(
                prompt,
                return_tensors="pt",
                truncation=True,
                max_length=config.max_length
            )

            if self.device == "cuda":
                inputs = {k: v.to(self.device) for k, v in inputs.items()}

            input_length = inputs["input_ids"].shape[1]

            # Prepare stopping criteria
            stopping_criteria = None
            all_stop_sequences = (stop_sequences or []) + (config.stop_sequences or [])
            if all_stop_sequences:
                stop_token_ids = [
                    self.tokenizer.encode(seq, add_special_tokens=False)
                    for seq in all_stop_sequences
                ]
                stopping_criteria = StoppingCriteriaList([
                    StopOnTokens(stop_token_ids)
                ])

            # Generate
            with torch.no_grad():
                outputs = await asyncio.to_thread(
                    self.model.generate,
                    **inputs,
                    max_new_tokens=config.max_length - input_length,
                    temperature=config.temperature if config.do_sample else 1.0,
                    top_p=config.top_p if config.do_sample else 1.0,
                    top_k=config.top_k if config.do_sample else 0,
                    repetition_penalty=config.repetition_penalty,
                    do_sample=config.do_sample,
                    num_return_sequences=config.num_return_sequences,
                    pad_token_id=self.tokenizer.pad_token_id,
                    eos_token_id=self.tokenizer.eos_token_id,
                    stopping_criteria=stopping_criteria
                )

            # Decode outputs
            generated_texts = []
            for output in outputs:
                generated_text = self.tokenizer.decode(
                    output[input_length:],
                    skip_special_tokens=True
                )
                # Remove stop sequences from output
                for stop_seq in all_stop_sequences:
                    if stop_seq in generated_text:
                        generated_text = generated_text[:generated_text.index(stop_seq)]
                generated_texts.append(generated_text)

            generation_time = (time.time() - start_time) * 1000
            output_length = outputs.shape[1] - input_length

            result = {
                "text": generated_texts[0] if len(generated_texts) == 1 else generated_texts,
                "tokens_used": input_length + output_length,
                "input_tokens": input_length,
                "output_tokens": output_length,
                "generation_time_ms": round(generation_time, 2),
                "model_name": self.model_info.name if self.model_info else settings.MODEL_NAME
            }

            logger.debug(
                "Generation completed",
                input_tokens=input_length,
                output_tokens=output_length,
                generation_time_ms=result["generation_time_ms"]
            )

            return result

        except Exception as e:
            logger.error("Generation failed", error=str(e))
            raise

    async def _manage_gpu_memory(self):
        """Manage GPU memory and clear cache if needed."""
        if not torch.cuda.is_available():
            return

        memory_allocated = torch.cuda.memory_allocated()
        memory_total = torch.cuda.get_device_properties(0).total_memory
        memory_ratio = memory_allocated / memory_total

        if memory_ratio > settings.CLEAR_CACHE_THRESHOLD:
            logger.warning(
                "GPU memory threshold exceeded, clearing cache",
                memory_ratio=round(memory_ratio, 2)
            )
            torch.cuda.empty_cache()
            gc.collect()

    def get_model_info(self) -> Optional[ModelInfo]:
        """Get information about the loaded model."""
        return self.model_info

    async def embed(self, text: str) -> List[float]:
        """
        Generate embeddings for text (if model supports it).

        Args:
            text: Input text

        Returns:
            List of embedding values
        """
        if not self.is_loaded:
            raise RuntimeError("Model not loaded")

        inputs = self.tokenizer(
            text,
            return_tensors="pt",
            truncation=True,
            max_length=settings.MAX_SEQUENCE_LENGTH
        )

        if self.device == "cuda":
            inputs = {k: v.to(self.device) for k, v in inputs.items()}

        with torch.no_grad():
            outputs = self.model(**inputs, output_hidden_states=True)
            # Use last hidden state mean as embedding
            embeddings = outputs.hidden_states[-1].mean(dim=1)
            return embeddings[0].cpu().tolist()
