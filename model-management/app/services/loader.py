"""
Dynamic model loading service.

Handles loading AI models into memory for inference.
"""

import gc
import logging
import time
from datetime import datetime
from typing import Any, Dict, Optional

from motor.motor_asyncio import AsyncIOMotorDatabase

from app.config import get_settings
from app.database import Database
from app.services.model_service import ModelService
from app.utils.encryption import get_encryption_service

logger = logging.getLogger(__name__)

settings = get_settings()


class ModelLoader:
    """Service for dynamically loading AI models."""

    def __init__(self, db: AsyncIOMotorDatabase):
        """
        Initialize the model loader.

        Args:
            db: MongoDB database instance
        """
        self.db = db
        self.model_service = ModelService(db)
        self._loaded_models: Dict[str, Dict[str, Any]] = {}
        self._load_order: list = []  # Track order for LRU eviction

    async def load_model(
        self,
        model_id: str,
        device: str = "cpu",
        dtype: Optional[str] = None,
    ) -> dict:
        """
        Load a model into memory.

        Args:
            model_id: Model ID to load
            device: Device to load model on (cpu, cuda, cuda:0, etc.)
            dtype: Data type for model weights

        Returns:
            Load result dictionary
        """
        start_time = time.time()

        try:
            # Check if already loaded
            if model_id in self._loaded_models:
                # Update access order for LRU
                if model_id in self._load_order:
                    self._load_order.remove(model_id)
                self._load_order.append(model_id)

                return {
                    "model_id": model_id,
                    "loaded": True,
                    "device": self._loaded_models[model_id]["device"],
                    "memory_usage_mb": self._loaded_models[model_id]["memory_mb"],
                    "load_time_seconds": 0,
                    "message": "Model already loaded",
                }

            # Check if we need to evict models
            if len(self._loaded_models) >= settings.MAX_LOADED_MODELS:
                await self._evict_lru_model()

            # Get model info
            model = await self.model_service.get_model(model_id)
            if not model:
                return {
                    "model_id": model_id,
                    "loaded": False,
                    "device": device,
                    "memory_usage_mb": 0,
                    "load_time_seconds": time.time() - start_time,
                    "message": "Model not found",
                }

            # Get file path (handles decryption)
            file_path = await self.model_service.get_model_file_path(model_id)
            if not file_path:
                return {
                    "model_id": model_id,
                    "loaded": False,
                    "device": device,
                    "memory_usage_mb": 0,
                    "load_time_seconds": time.time() - start_time,
                    "message": "Model file not found",
                }

            # Load based on framework
            framework = model.framework.value
            loaded_model, memory_mb = await self._load_by_framework(
                file_path, framework, device, dtype
            )

            # Store loaded model
            self._loaded_models[model_id] = {
                "model": loaded_model,
                "device": device,
                "framework": framework,
                "memory_mb": memory_mb,
                "loaded_at": datetime.utcnow(),
                "file_path": file_path,
            }
            self._load_order.append(model_id)

            load_time = time.time() - start_time

            logger.info(
                f"Model loaded: {model_id} on {device} "
                f"({memory_mb:.2f}MB, {load_time:.2f}s)"
            )

            return {
                "model_id": model_id,
                "loaded": True,
                "device": device,
                "memory_usage_mb": memory_mb,
                "load_time_seconds": load_time,
                "message": "Model loaded successfully",
            }

        except Exception as e:
            load_time = time.time() - start_time
            error_msg = str(e)
            logger.error(f"Failed to load model {model_id}: {error_msg}")

            return {
                "model_id": model_id,
                "loaded": False,
                "device": device,
                "memory_usage_mb": 0,
                "load_time_seconds": load_time,
                "message": f"Load failed: {error_msg}",
            }

    async def _load_by_framework(
        self,
        file_path: str,
        framework: str,
        device: str,
        dtype: Optional[str],
    ) -> tuple:
        """
        Load model based on framework.

        Args:
            file_path: Path to model file
            framework: ML framework
            device: Target device
            dtype: Data type

        Returns:
            Tuple of (loaded_model, memory_mb)
        """
        memory_before = self._get_memory_usage()

        if framework in ["pytorch", "huggingface"]:
            model = await self._load_pytorch_model(file_path, device, dtype)
        elif framework == "tensorflow":
            model = await self._load_tensorflow_model(file_path, device)
        elif framework == "onnx":
            model = await self._load_onnx_model(file_path, device)
        else:
            # Generic pickle load
            model = await self._load_pickle_model(file_path)

        memory_after = self._get_memory_usage()
        memory_mb = max(0, memory_after - memory_before)

        return model, memory_mb

    async def _load_pytorch_model(
        self, file_path: str, device: str, dtype: Optional[str]
    ) -> Any:
        """Load a PyTorch model."""
        try:
            import torch

            # Determine device
            if device.startswith("cuda") and not torch.cuda.is_available():
                logger.warning("CUDA not available, falling back to CPU")
                device = "cpu"

            # Load model
            model = torch.load(file_path, map_location=device)

            # Set data type if specified
            if dtype and hasattr(model, "to"):
                dtype_map = {
                    "float16": torch.float16,
                    "float32": torch.float32,
                    "float64": torch.float64,
                    "bfloat16": torch.bfloat16,
                }
                if dtype in dtype_map:
                    model = model.to(dtype_map[dtype])

            # Set to evaluation mode if it's a nn.Module
            if hasattr(model, "eval"):
                model.eval()

            return model

        except ImportError:
            raise ImportError("PyTorch is not installed")

    async def _load_tensorflow_model(self, file_path: str, device: str) -> Any:
        """Load a TensorFlow model."""
        try:
            import tensorflow as tf

            # Configure device
            if device == "cpu":
                with tf.device("/CPU:0"):
                    model = tf.keras.models.load_model(file_path)
            else:
                model = tf.keras.models.load_model(file_path)

            return model

        except ImportError:
            raise ImportError("TensorFlow is not installed")

    async def _load_onnx_model(self, file_path: str, device: str) -> Any:
        """Load an ONNX model."""
        try:
            import onnxruntime as ort

            # Configure providers based on device
            if device.startswith("cuda"):
                providers = ["CUDAExecutionProvider", "CPUExecutionProvider"]
            else:
                providers = ["CPUExecutionProvider"]

            session = ort.InferenceSession(file_path, providers=providers)
            return session

        except ImportError:
            raise ImportError("ONNX Runtime is not installed")

    async def _load_pickle_model(self, file_path: str) -> Any:
        """Load a pickle model."""
        import pickle

        with open(file_path, "rb") as f:
            model = pickle.load(f)

        return model

    async def unload_model(self, model_id: str) -> bool:
        """
        Unload a model from memory.

        Args:
            model_id: Model ID to unload

        Returns:
            True if unloaded, False if not loaded
        """
        if model_id not in self._loaded_models:
            return False

        # Remove from loaded models
        model_info = self._loaded_models.pop(model_id)

        # Remove from load order
        if model_id in self._load_order:
            self._load_order.remove(model_id)

        # Clean up model
        model = model_info.get("model")
        if model is not None:
            del model

        # Force garbage collection
        gc.collect()

        # Clear CUDA cache if using GPU
        try:
            import torch
            if torch.cuda.is_available():
                torch.cuda.empty_cache()
        except ImportError:
            pass

        logger.info(f"Model unloaded: {model_id}")
        return True

    async def _evict_lru_model(self) -> None:
        """Evict least recently used model."""
        if not self._load_order:
            return

        # Get LRU model (first in order)
        lru_model_id = self._load_order[0]
        await self.unload_model(lru_model_id)
        logger.info(f"Evicted LRU model: {lru_model_id}")

    async def get_model(self, model_id: str) -> Optional[Any]:
        """
        Get a loaded model.

        Args:
            model_id: Model ID

        Returns:
            Loaded model or None
        """
        if model_id in self._loaded_models:
            # Update access order for LRU
            if model_id in self._load_order:
                self._load_order.remove(model_id)
            self._load_order.append(model_id)

            return self._loaded_models[model_id]["model"]
        return None

    async def get_loaded_models(self) -> list:
        """
        Get information about loaded models.

        Returns:
            List of loaded model info
        """
        result = []
        for model_id, info in self._loaded_models.items():
            result.append({
                "model_id": model_id,
                "device": info["device"],
                "framework": info["framework"],
                "memory_mb": info["memory_mb"],
                "loaded_at": info["loaded_at"].isoformat(),
            })
        return result

    async def get_total_memory_usage(self) -> float:
        """
        Get total memory usage of loaded models.

        Returns:
            Total memory in MB
        """
        return sum(info["memory_mb"] for info in self._loaded_models.values())

    async def clear_all(self) -> int:
        """
        Unload all models.

        Returns:
            Number of models unloaded
        """
        count = len(self._loaded_models)
        model_ids = list(self._loaded_models.keys())

        for model_id in model_ids:
            await self.unload_model(model_id)

        logger.info(f"Cleared all {count} loaded models")
        return count

    def _get_memory_usage(self) -> float:
        """Get current process memory usage in MB."""
        try:
            import psutil
            process = psutil.Process()
            return process.memory_info().rss / (1024 * 1024)
        except ImportError:
            return 0

    async def predict(
        self,
        model_id: str,
        input_data: Any,
        **kwargs,
    ) -> dict:
        """
        Run prediction with a loaded model.

        Args:
            model_id: Model ID
            input_data: Input data for prediction
            **kwargs: Additional arguments

        Returns:
            Prediction result
        """
        model = await self.get_model(model_id)
        if model is None:
            # Try to load the model
            load_result = await self.load_model(model_id)
            if not load_result["loaded"]:
                return {
                    "success": False,
                    "output": None,
                    "error": load_result["message"],
                }
            model = await self.get_model(model_id)

        try:
            start_time = time.time()

            # Run prediction based on model type
            if hasattr(model, "predict"):
                output = model.predict(input_data, **kwargs)
            elif hasattr(model, "__call__"):
                output = model(input_data, **kwargs)
            elif hasattr(model, "run"):
                # ONNX runtime
                output = model.run(None, input_data)
            else:
                return {
                    "success": False,
                    "output": None,
                    "error": "Model does not have predict, __call__, or run method",
                }

            inference_time = time.time() - start_time

            return {
                "success": True,
                "output": output,
                "inference_time_ms": inference_time * 1000,
                "error": None,
            }

        except Exception as e:
            error_msg = str(e)
            logger.error(f"Prediction failed for model {model_id}: {error_msg}")
            return {
                "success": False,
                "output": None,
                "error": error_msg,
            }


# Global instance
_model_loader: Optional[ModelLoader] = None


async def get_model_loader() -> ModelLoader:
    """
    FastAPI dependency to get model loader.

    Returns:
        ModelLoader instance
    """
    global _model_loader
    if _model_loader is None:
        db = Database.get_db()
        _model_loader = ModelLoader(db)
    return _model_loader
