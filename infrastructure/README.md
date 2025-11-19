# Infrastructure Module

Module 6 of the AI Platform - Parallel Processing and Load Balancing

## Overview

The Infrastructure Module provides distributed computing capabilities using Ray, load balancing with NGINX, and automatic scaling based on workload metrics. It handles parallel task execution, resource management, and cluster health monitoring.

## Features

- **Distributed Computing**: Ray-based task distribution and execution
- **Load Balancing**: NGINX-based request distribution with multiple algorithms
- **Auto-Scaling**: Automatic worker scaling based on CPU, memory, and queue depth
- **Health Monitoring**: Continuous monitoring of cluster components
- **Resource Management**: Dynamic resource allocation and reservation
- **Metrics Collection**: Comprehensive performance metrics and alerting

## Architecture

```
                    +-------------------+
                    |      NGINX        |
                    |  Load Balancer    |
                    +--------+----------+
                             |
              +--------------+--------------+
              |                             |
    +---------v---------+     +------------v---------+
    | Infrastructure    |     | Infrastructure       |
    | Instance 1        |     | Instance 2           |
    +---------+---------+     +------------+---------+
              |                             |
              +--------------+--------------+
                             |
                    +--------v--------+
                    |   Ray Cluster   |
                    |  (Head + Workers)|
                    +-----------------+
```

## Directory Structure

```
infrastructure/
├── app/
│   ├── __init__.py
│   ├── main.py                 # FastAPI application entry point
│   ├── config.py               # Configuration settings
│   ├── services/
│   │   ├── __init__.py
│   │   ├── ray_service.py      # Ray cluster management
│   │   ├── load_balancer.py    # Load balancing logic
│   │   ├── health_monitor.py   # Health monitoring
│   │   ├── autoscaler.py       # Auto-scaling service
│   │   └── resource_manager.py # Resource allocation
│   ├── api/
│   │   └── v1/
│   │       ├── tasks.py        # Task submission endpoints
│   │       ├── workers.py      # Worker management
│   │       ├── metrics.py      # Metrics endpoints
│   │       └── scaling.py      # Scaling configuration
│   └── utils/
│       └── metrics_collector.py
├── nginx/
│   ├── nginx.conf              # NGINX configuration
│   └── upstream.conf           # Upstream servers
├── kubernetes/
│   ├── deployment.yaml
│   ├── service.yaml
│   ├── hpa.yaml
│   └── configmap.yaml
├── requirements.txt
├── requirements-dev.txt
├── .env.example
├── Dockerfile
├── docker-compose.yml
└── README.md
```

## Quick Start

### Prerequisites

- Python 3.9+
- Docker and Docker Compose
- Redis
- Apache Kafka

### Local Development

1. **Clone and setup**:
   ```bash
   cd infrastructure
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   pip install -r requirements-dev.txt
   ```

2. **Configure environment**:
   ```bash
   cp .env.example .env
   # Edit .env with your configuration
   ```

3. **Start dependencies**:
   ```bash
   docker-compose up -d redis kafka ray-head ray-worker
   ```

4. **Run the application**:
   ```bash
   uvicorn app.main:app --reload --port 8006
   ```

5. **Access the API**:
   - API: http://localhost:8006
   - Docs: http://localhost:8006/docs
   - Health: http://localhost:8006/health
   - Ray Dashboard: http://localhost:8265

### Docker Deployment

```bash
# Build and start all services
docker-compose up -d --build

# View logs
docker-compose logs -f infrastructure

# Scale workers
docker-compose up -d --scale ray-worker=4
```

### Kubernetes Deployment

```bash
# Create namespace
kubectl apply -f kubernetes/configmap.yaml

# Deploy
kubectl apply -f kubernetes/deployment.yaml
kubectl apply -f kubernetes/service.yaml
kubectl apply -f kubernetes/hpa.yaml

# Check status
kubectl get pods -n ai-platform
kubectl get hpa -n ai-platform
```

## API Endpoints

### Tasks

| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/api/v1/tasks/submit` | Submit a new task |
| GET | `/api/v1/tasks/{task_id}` | Get task status |
| GET | `/api/v1/tasks/{task_id}/result` | Get task result |
| POST | `/api/v1/tasks/{task_id}/cancel` | Cancel a task |
| GET | `/api/v1/tasks/` | List all tasks |
| POST | `/api/v1/tasks/cleanup` | Cleanup old tasks |

### Workers

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/api/v1/workers/` | List all workers |
| GET | `/api/v1/workers/{worker_id}` | Get worker info |
| PATCH | `/api/v1/workers/{worker_id}` | Update worker status |
| POST | `/api/v1/workers/scale` | Scale workers |
| GET | `/api/v1/workers/nodes/list` | List cluster nodes |
| GET | `/api/v1/workers/resources` | Get cluster resources |

### Metrics

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/api/v1/metrics/cluster` | Get cluster metrics |
| GET | `/api/v1/metrics/tasks` | Get task metrics |
| GET | `/api/v1/metrics/resources` | Get resource metrics |
| GET | `/api/v1/metrics/summary` | Get metrics summary |
| GET | `/api/v1/metrics/alerts` | Get health alerts |

### Scaling

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/api/v1/scaling/config` | Get scaling config |
| PATCH | `/api/v1/scaling/config` | Update scaling config |
| GET | `/api/v1/scaling/state` | Get current state |
| POST | `/api/v1/scaling/enable` | Enable auto-scaling |
| POST | `/api/v1/scaling/disable` | Disable auto-scaling |
| POST | `/api/v1/scaling/trigger` | Manual scale trigger |

## Configuration

### Auto-Scaling Thresholds

```python
AUTOSCALE_CPU_THRESHOLD_HIGH = 80.0    # Scale up when CPU > 80%
AUTOSCALE_CPU_THRESHOLD_LOW = 30.0     # Scale down when CPU < 30%
AUTOSCALE_MEMORY_THRESHOLD_HIGH = 85.0 # Scale up when memory > 85%
AUTOSCALE_QUEUE_THRESHOLD = 100        # Scale up when queue > 100 tasks
AUTOSCALE_COOLDOWN_PERIOD = 120        # Wait 2 min between scaling actions
```

### Worker Limits

```python
MIN_WORKERS = 1
MAX_WORKERS = 10
WORKER_CPU_FRACTION = 0.25
WORKER_MEMORY_MB = 1024
```

## Load Balancing Algorithms

The load balancer supports multiple algorithms:

- **Round Robin**: Distribute requests evenly
- **Least Connections**: Route to least busy server
- **Weighted Round Robin**: Consider server weights
- **IP Hash**: Session persistence by client IP
- **Least Response Time**: Route to fastest server

## Monitoring

### Health Checks

- `/health`: Overall service health
- `/ready`: Readiness for traffic

### Metrics Export

The module supports Prometheus-format metrics export at `/api/v1/metrics/prometheus`.

### Alerts

Health alerts are generated for:
- Ray cluster connectivity issues
- High resource utilization
- Worker failures
- Scaling events

## Testing

```bash
# Run all tests
pytest

# Run with coverage
pytest --cov=app --cov-report=html

# Run specific tests
pytest tests/unit/test_ray_service.py -v
```

## Troubleshooting

### Ray Connection Issues

```bash
# Check Ray cluster status
ray status

# View Ray logs
docker-compose logs ray-head
```

### High Memory Usage

- Check for memory leaks in tasks
- Adjust `WORKER_MEMORY_MB`
- Enable task result cleanup

### Scaling Not Working

- Verify `AUTOSCALE_ENABLED=True`
- Check cooldown period hasn't elapsed
- Review scaling thresholds

## Contributing

1. Create a feature branch
2. Write tests for new functionality
3. Ensure all tests pass
4. Submit a pull request

## License

Copyright (c) 2024 AI Platform Development Team
