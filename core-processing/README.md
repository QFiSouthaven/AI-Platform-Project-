# Core Processing Module

AI-driven code generation, debugging, and optimization using Large Language Models (LLMs).

## Overview

The Core Processing module is responsible for:
- **Code Generation**: Generate code from natural language descriptions
- **Debugging**: Analyze code for bugs and provide fixes
- **Optimization**: Optimize code for performance, readability, and security
- **Evaluation**: Evaluate code quality and provide improvement suggestions

## Architecture

```
core-processing/
├── app/
│   ├── main.py              # FastAPI application entry point
│   ├── config.py            # Configuration settings
│   ├── models/              # Pydantic models
│   │   ├── llm_models.py    # LLM request/response models
│   │   └── evaluation.py    # Evaluation metrics models
│   ├── services/            # Business logic
│   │   ├── llm_service.py   # Hugging Face model integration
│   │   ├── code_generator.py
│   │   ├── debugger.py
│   │   ├── optimizer.py
│   │   └── evaluator.py
│   ├── agents/              # Multi-agent system
│   │   ├── code_agent.py
│   │   ├── debug_agent.py
│   │   └── coordinator.py
│   ├── api/v1/              # API endpoints
│   │   ├── generate.py
│   │   ├── debug.py
│   │   ├── optimize.py
│   │   └── evaluate.py
│   ├── kafka/               # Kafka integration
│   │   ├── consumer.py
│   │   └── producer.py
│   └── utils/               # Utilities
│       ├── code_parser.py
│       └── prompt_templates.py
├── tests/
├── requirements.txt
├── Dockerfile
└── README.md
```

## Features

### Code Generation
- Support for multiple programming languages (Python, JavaScript, TypeScript, Java, Go, Rust)
- Different task types (function, class, module, test, documentation)
- Few-shot learning with examples
- Code completion

### Debugging
- Error analysis and explanation
- Bug detection and automatic fixes
- Stack trace analysis
- Test suggestions

### Optimization
- Performance optimization
- Readability improvements
- Memory optimization
- Security hardening
- Code refactoring

### Evaluation
- Quality scores (readability, maintainability, performance, security)
- Code metrics (complexity, LOC, comment ratio)
- Issue detection
- Improvement suggestions

### Multi-Agent System
- Code generation agent with planning and self-review
- Debug agent with pattern learning
- Coordinator for complex workflows

## Quick Start

### Prerequisites

- Python 3.9+
- CUDA-capable GPU (recommended for production)
- Docker (optional)
- Kafka (for async processing)

### Installation

1. Clone the repository:
```bash
cd AI-Platform-Project-/core-processing
```

2. Create virtual environment:
```bash
python -m venv venv
source venv/bin/activate  # Linux/Mac
# or
venv\Scripts\activate  # Windows
```

3. Install dependencies:
```bash
pip install -r requirements.txt
```

4. Configure environment:
```bash
cp .env.example .env
# Edit .env with your settings
```

5. Run the application:
```bash
uvicorn app.main:app --reload
```

### Using Docker

Build and run with CPU:
```bash
docker build --target production-cpu -t core-processing:cpu .
docker run -p 8000:8000 --env-file .env core-processing:cpu
```

Build and run with GPU:
```bash
docker build --target production-gpu -t core-processing:gpu .
docker run --gpus all -p 8000:8000 --env-file .env core-processing:gpu
```

## API Usage

### Code Generation

```bash
curl -X POST "http://localhost:8000/api/v1/generate/" \
  -H "Content-Type: application/json" \
  -d '{
    "prompt": "Create a function to calculate fibonacci numbers",
    "language": "python",
    "task_type": "function"
  }'
```

### Debugging

```bash
curl -X POST "http://localhost:8000/api/v1/debug/" \
  -H "Content-Type: application/json" \
  -d '{
    "code": "def divide(a, b):\n    return a / b",
    "language": "python",
    "error_message": "ZeroDivisionError: division by zero"
  }'
```

### Optimization

```bash
curl -X POST "http://localhost:8000/api/v1/optimize/" \
  -H "Content-Type: application/json" \
  -d '{
    "code": "result = []\nfor i in range(100):\n    result.append(i * 2)",
    "language": "python",
    "optimization_goals": ["performance", "readability"]
  }'
```

### Evaluation

```bash
curl -X POST "http://localhost:8000/api/v1/evaluate/" \
  -H "Content-Type: application/json" \
  -d '{
    "code": "def add(a, b):\n    return a + b",
    "language": "python"
  }'
```

## API Documentation

Once running, access the interactive API documentation:
- Swagger UI: http://localhost:8000/docs
- ReDoc: http://localhost:8000/redoc
- OpenAPI JSON: http://localhost:8000/openapi.json

## Configuration

Key environment variables:

| Variable | Description | Default |
|----------|-------------|---------|
| `MODEL_NAME` | Hugging Face model name | `bigcode/starcoder` |
| `HF_API_TOKEN` | Hugging Face API token | - |
| `USE_GPU` | Enable GPU inference | `True` |
| `MAX_SEQUENCE_LENGTH` | Maximum token length | `2048` |
| `TEMPERATURE` | Generation temperature | `0.7` |
| `KAFKA_BOOTSTRAP_SERVERS` | Kafka servers | `localhost:9092` |

See `.env.example` for all available options.

## Supported Models

The module supports various code LLMs:
- **StarCoder** (bigcode/starcoder) - Recommended
- **CodeLlama** (codellama/CodeLlama-7b-hf)
- **WizardCoder** (WizardLM/WizardCoder-15B-V1.0)
- **Mistral** (mistralai/Mistral-7B-v0.1)

## Kafka Integration

The module supports async processing via Kafka:

**Topics:**
- `processing.code.generation.request` / `.result`
- `processing.code.debug.request` / `.result`
- `processing.code.optimize.request` / `.result`
- `processing.code.evaluate.request` / `.result`

**Message Format:**
```json
{
  "schema_version": "1.0",
  "event_type": "generation",
  "timestamp": "2024-01-15T10:30:00Z",
  "data": {...},
  "metadata": {
    "correlation_id": "uuid",
    "source": "core-processing"
  }
}
```

## Health Checks

- `/health` - Detailed health status
- `/ready` - Readiness probe (for Kubernetes)
- `/live` - Liveness probe (for Kubernetes)

## Testing

Run tests:
```bash
# Install dev dependencies
pip install -r requirements-dev.txt

# Run tests
pytest

# Run with coverage
pytest --cov=app --cov-report=html
```

## Development

### Code Style

```bash
# Format code
black app/
isort app/

# Lint
flake8 app/
mypy app/
```

### Pre-commit Hooks

```bash
pre-commit install
pre-commit run --all-files
```

## Troubleshooting

### Model Loading Issues
- Ensure `HF_API_TOKEN` is set for gated models
- Check available GPU memory
- Try enabling `LOAD_IN_8BIT` or `LOAD_IN_4BIT` for quantization

### Kafka Connection Issues
- Verify `KAFKA_BOOTSTRAP_SERVERS` is correct
- Check Kafka is running and accessible
- Review Kafka logs for errors

### GPU Memory Errors
- Reduce `MAX_SEQUENCE_LENGTH`
- Enable quantization (`LOAD_IN_8BIT=True`)
- Set `MAX_GPU_MEMORY_MB` to limit usage

## Performance Tuning

- Use GPU with sufficient VRAM (16GB+ recommended)
- Enable quantization for memory efficiency
- Adjust `CLEAR_CACHE_THRESHOLD` for memory management
- Use batch endpoints for multiple requests

## License

MIT License - see LICENSE file for details.

## Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Run tests and linting
5. Submit a pull request

## Support

For issues and feature requests, please use the GitHub issue tracker.
