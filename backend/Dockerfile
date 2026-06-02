# Multi-stage Dockerfile for AWS Lambda deployment
# Uses AWS Lambda Web Adapter to run FastAPI unchanged on Lambda
# Also works for local development with docker-compose
#
# For Lambda deployment, the SAM template handles the Lambda Web Adapter layer.
# This Dockerfile produces an image compatible with both Lambda and standard containers.

# Build stage
FROM python:3.11-slim AS builder

WORKDIR /build

COPY requirements.txt .
RUN pip install --no-cache-dir --prefix=/install -r requirements.txt

# Runtime stage
FROM python:3.11-slim AS runtime

# Security: run as non-root user (for local dev; Lambda ignores this)
RUN groupadd -r appuser && useradd -r -g appuser -d /app -s /sbin/nologin appuser

# Install system dependencies for Pillow
RUN apt-get update && \
    apt-get install -y --no-install-recommends \
    libpng-dev \
    libjpeg-dev \
    libfreetype6-dev \
    fonts-dejavu-core \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# Copy installed packages from builder
COPY --from=builder /install /usr/local

# Copy application code
COPY . .

# Create directories for uploads and generated images
RUN mkdir -p uploads/logos generated_images && \
    chown -R appuser:appuser /app

USER appuser

# Port configuration
# Lambda Web Adapter (applied via Lambda layer) forwards requests to this port
ENV PORT=8000

ENV PYTHONUNBUFFERED=1
ENV PYTHONDONTWRITEBYTECODE=1

EXPOSE ${PORT}

# Health check (used by docker-compose for local dev)
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD python -c "import urllib.request; urllib.request.urlopen('http://localhost:${PORT}/health')" || exit 1

# Start the application
# Lambda Web Adapter intercepts requests and forwards to this process
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000", "--workers", "1"]
