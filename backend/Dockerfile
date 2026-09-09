# ==========================================
# CropHealthAI Backend Dockerfile
# ==========================================
FROM python:3.11-slim

WORKDIR /app

# Prevent Python from writing .pyc files and buffering stdout
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PYTHONPATH=/app

# Install system dependencies (build tools, PostgreSQL client, curl for health checks)
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    libpq-dev \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements and install dependencies
COPY requirements.txt* backend/requirements.txt* /tmp/
RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir -r /tmp/requirements.txt

# Copy source code and ensure consistent /app/backend structure
COPY . /tmp/src
RUN if [ -d /tmp/src/backend ]; then \
        cp -r /tmp/src/backend /app/backend; \
    else \
        mkdir -p /app/backend && cp -r /tmp/src/* /app/backend/; \
    fi && rm -rf /tmp/src

# Ensure storage directories exist
RUN mkdir -p /app/backend/storage/uploads \
             /app/backend/storage/overlays \
             /app/backend/storage/thumbnails

# Expose backend port
EXPOSE 8000

# Container healthcheck
HEALTHCHECK --interval=20s --timeout=5s --start-period=10s --retries=3 \
  CMD curl -f http://localhost:8000/health || exit 1

# Run FastAPI backend via Uvicorn
CMD ["uvicorn", "backend.app.main:app", "--host", "0.0.0.0", "--port", "8000"]
