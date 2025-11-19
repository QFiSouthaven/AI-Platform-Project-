# Multi-stage Dockerfile for Core Processing Module
# Supports both CPU and GPU builds

# ============================================
# Stage 1: Base image with dependencies
# ============================================
FROM python:3.9-slim as base

# Set environment variables
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1

# Install system dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    curl \
    git \
    && rm -rf /var/lib/apt/lists/*

# Create app user
RUN groupadd -r appuser && useradd -r -g appuser appuser

# Set work directory
WORKDIR /app

# ============================================
# Stage 2: Dependencies
# ============================================
FROM base as dependencies

# Copy requirements first for better caching
COPY requirements.txt .

# Install Python dependencies
RUN pip install --no-cache-dir -r requirements.txt

# ============================================
# Stage 3: Production image (CPU)
# ============================================
FROM dependencies as production-cpu

# Copy application code
COPY --chown=appuser:appuser app/ ./app/
COPY --chown=appuser:appuser .env.example ./.env.example

# Create necessary directories
RUN mkdir -p /tmp/model_cache && chown -R appuser:appuser /tmp/model_cache

# Switch to non-root user
USER appuser

# Expose port
EXPOSE 8000

# Health check
HEALTHCHECK --interval=30s --timeout=30s --start-period=60s --retries=3 \
    CMD curl -f http://localhost:8000/health || exit 1

# Run the application
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]

# ============================================
# Stage 4: Production image (GPU)
# ============================================
FROM nvidia/cuda:11.8-cudnn8-runtime-ubuntu22.04 as production-gpu

# Set environment variables
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1 \
    DEBIAN_FRONTEND=noninteractive

# Install system dependencies and Python
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    curl \
    git \
    python3.9 \
    python3.9-dev \
    python3-pip \
    && rm -rf /var/lib/apt/lists/* \
    && ln -s /usr/bin/python3.9 /usr/bin/python

# Create app user
RUN groupadd -r appuser && useradd -r -g appuser appuser

# Set work directory
WORKDIR /app

# Copy requirements and install dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Install PyTorch with CUDA support
RUN pip install --no-cache-dir torch==2.1.2+cu118 --index-url https://download.pytorch.org/whl/cu118

# Copy application code
COPY --chown=appuser:appuser app/ ./app/
COPY --chown=appuser:appuser .env.example ./.env.example

# Create necessary directories
RUN mkdir -p /tmp/model_cache && chown -R appuser:appuser /tmp/model_cache

# Switch to non-root user
USER appuser

# Expose port
EXPOSE 8000

# Health check
HEALTHCHECK --interval=30s --timeout=30s --start-period=120s --retries=3 \
    CMD curl -f http://localhost:8000/health || exit 1

# Run the application
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]

# ============================================
# Stage 5: Development image
# ============================================
FROM dependencies as development

# Install development dependencies
COPY requirements-dev.txt .
RUN pip install --no-cache-dir -r requirements-dev.txt

# Copy application code
COPY --chown=appuser:appuser . .

# Create necessary directories
RUN mkdir -p /tmp/model_cache && chown -R appuser:appuser /tmp/model_cache

# Switch to non-root user
USER appuser

# Expose port
EXPOSE 8000

# Run with reload for development
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000", "--reload"]
