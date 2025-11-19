# Model Management Module

AI Platform module for storing, loading, and managing AI models with plugin support, versioning, and encryption capabilities.

## Features

- **Model Storage**: Store and manage AI models with metadata
- **Dynamic Loading**: Load models into memory for inference
- **Versioning**: Track model versions with lineage and rollback support
- **Encryption**: Encrypt model files at rest with key rotation
- **Plugin System**: Extend functionality with custom plugins
- **Multi-Framework Support**: PyTorch, TensorFlow, ONNX, and more

## Architecture

```
model-management/
├── app/
│   ├── main.py              # FastAPI application
│   ├── config.py            # Configuration settings
│   ├── database.py          # MongoDB connection
│   ├── models/              # Pydantic schemas
│   ├── services/            # Business logic
│   ├── api/v1/              # REST endpoints
│   └── utils/               # Utilities
├── tests/                   # Test suite
├── requirements.txt         # Dependencies
├── Dockerfile              # Container build
└── docker-compose.yml      # Local development
```

## Quick Start

### Prerequisites

- Python 3.9+
- MongoDB 6.0+
- Redis (optional, for caching)
- Docker and Docker Compose (optional)

### Installation

1. Clone the repository:
```bash
cd model-management
```

2. Create virtual environment:
```bash
python -m venv venv
source venv/bin/activate  # Linux/Mac
# or
venv\Scripts\activate     # Windows
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

5. Run the service:
```bash
python -m app.main
```

### Docker Deployment

```bash
# Build and run all services
docker-compose up -d

# View logs
docker-compose logs -f model-management

# Stop services
docker-compose down
```

## API Documentation

Once running, access the API documentation at:
- Swagger UI: http://localhost:8005/docs
- ReDoc: http://localhost:8005/redoc

## API Endpoints

### Models

| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/api/v1/models` | Create a new model |
| GET | `/api/v1/models` | List all models |
| GET | `/api/v1/models/{id}` | Get model by ID |
| PATCH | `/api/v1/models/{id}` | Update model |
| DELETE | `/api/v1/models/{id}` | Delete model |
| GET | `/api/v1/models/{id}/download` | Download model file |
| POST | `/api/v1/models/{id}/load` | Load model into memory |
| POST | `/api/v1/models/{id}/unload` | Unload model from memory |

### Plugins

| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/api/v1/plugins` | Create a new plugin |
| GET | `/api/v1/plugins` | List all plugins |
| GET | `/api/v1/plugins/{id}` | Get plugin by ID |
| PATCH | `/api/v1/plugins/{id}` | Update plugin |
| DELETE | `/api/v1/plugins/{id}` | Delete plugin |
| POST | `/api/v1/plugins/{id}/load` | Load plugin |
| POST | `/api/v1/plugins/{id}/execute` | Execute plugin |

### Versions

| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/api/v1/versions` | Create a new version |
| GET | `/api/v1/versions/model/{id}` | List versions for model |
| GET | `/api/v1/versions/{id}` | Get version by ID |
| POST | `/api/v1/versions/{id}/activate` | Activate version |
| POST | `/api/v1/versions/compare` | Compare two versions |
| POST | `/api/v1/versions/rollback` | Rollback to previous version |

## Usage Examples

### Upload a Model

```python
import httpx

with open("model.pt", "rb") as f:
    response = httpx.post(
        "http://localhost:8005/api/v1/models",
        files={"file": ("model.pt", f)},
        data={
            "name": "my-classifier",
            "version": "1.0.0",
            "model_type": "classification",
            "framework": "pytorch",
            "description": "Image classification model",
            "tags": "image,classification,resnet",
            "created_by": "user@example.com",
            "encrypted": "true",
        },
    )

print(response.json())
```

### Load and Use a Model

```python
import httpx

# Load model
response = httpx.post(
    "http://localhost:8005/api/v1/models/model_id/load",
    json={"model_id": "model_id", "device": "cuda"}
)

# Check loaded models
response = httpx.get("http://localhost:8005/api/v1/models/loaded/list")
print(response.json())
```

### Create a Plugin

```python
# plugin.py
class MyPreprocessor:
    def __init__(self, config):
        self.config = config

    def execute(self, data):
        # Process data
        return processed_data
```

```python
import httpx

with open("plugin.py", "rb") as f:
    response = httpx.post(
        "http://localhost:8005/api/v1/plugins",
        files={"file": ("plugin.py", f)},
        data={
            "name": "my-preprocessor",
            "plugin_type": "preprocessor",
            "entry_point": "plugin:MyPreprocessor",
            "created_by": "user@example.com",
        },
    )
```

## Configuration

### Environment Variables

| Variable | Description | Default |
|----------|-------------|---------|
| `MONGODB_URI` | MongoDB connection URI | `mongodb://localhost:27017` |
| `MONGODB_DB_NAME` | Database name | `model_management` |
| `MODEL_STORAGE_PATH` | Model file storage path | `/data/models` |
| `ENABLE_ENCRYPTION` | Enable model encryption | `True` |
| `MAX_LOADED_MODELS` | Maximum models in memory | `10` |
| `MAX_VERSIONS_PER_MODEL` | Maximum versions per model | `100` |

See `.env.example` for all configuration options.

## Encryption

Model files can be encrypted at rest using Fernet symmetric encryption.

### Key Management

- Keys are stored in `ENCRYPTION_KEY_PATH`
- Supports key rotation via `/encryption/rotate` endpoint
- Old keys are retained for decrypting existing files

### Rotate Keys

```bash
curl -X POST http://localhost:8005/encryption/rotate
```

## Testing

```bash
# Install dev dependencies
pip install -r requirements-dev.txt

# Run tests
pytest

# Run with coverage
pytest --cov=app --cov-report=html

# Run specific test file
pytest tests/unit/test_model_service.py
```

## Development

### Code Quality

```bash
# Format code
black app tests

# Sort imports
isort app tests

# Lint
flake8 app tests

# Type check
mypy app
```

### Pre-commit Hooks

```bash
pre-commit install
pre-commit run --all-files
```

## Health Checks

- Health: `GET /health`
- Ready: `GET /ready`
- Info: `GET /info`

## Monitoring

The service exposes metrics and health information:

```bash
# Health status
curl http://localhost:8005/health

# Storage statistics
curl http://localhost:8005/storage/stats
```

## Security

- All model files can be encrypted at rest
- API authentication via JWT tokens
- Input validation on all endpoints
- Secure file handling with checksums

## License

Copyright (c) 2024 AI Platform Development Team

## Support

For issues and feature requests, please use the GitHub issue tracker.
