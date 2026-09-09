#!/usr/bin/env bash
# ==============================================================================
# CropHealthAI - Local Development Startup Script
# Builds containers and starts the full stack (PostgreSQL, Redis, Backend, Frontend, pgAdmin)
# ==============================================================================

set -eo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
ROOT_DIR="$(cd "${SCRIPT_DIR}/.." && pwd)"

cd "${ROOT_DIR}"

echo "=========================================================="
echo "  🌿 Starting CropHealthAI Full Stack via Docker Compose"
echo "=========================================================="

# 1. Check Docker Daemon availability
if ! command -v docker &> /dev/null; then
    echo "❌ Error: Docker is not installed or not in PATH."
    echo "Please install Docker Desktop: https://www.docker.com/products/docker-desktop"
    exit 1
fi

if ! docker info &> /dev/null; then
    echo "❌ Error: Docker daemon is not running. Please start Docker."
    exit 1
fi

# 2. Determine docker-compose command (v2 plugin or legacy binary)
if docker compose version &> /dev/null; then
    COMPOSE_CMD="docker compose"
elif command -v docker-compose &> /dev/null; then
    COMPOSE_CMD="docker-compose"
else
    echo "❌ Error: Neither 'docker compose' nor 'docker-compose' was found."
    exit 1
fi

# 3. Ensure environment files exist
if [ ! -f "backend/.env" ] && [ -f "backend/.env.example" ]; then
    echo "📋 Creating backend/.env from sample..."
    cp backend/.env.example backend/.env
fi

if [ ! -f "frontend/.env" ] && [ -f "frontend/.env.example" ]; then
    echo "📋 Creating frontend/.env from sample..."
    cp frontend/.env.example frontend/.env
fi

# 4. Launch Stack with build
echo "🚀 Building and launching containers..."
echo "Services will be accessible at:"
echo "  - Frontend Web UI:  http://localhost:3000"
echo "  - Backend API:      http://localhost:8000"
echo "  - Swagger API Docs: http://localhost:8000/docs"
echo "  - pgAdmin:          http://localhost:5050 (User: admin@crophealth.ai / Pass: admin)"
echo "  - PostgreSQL:       localhost:5432"
echo "  - Redis:            localhost:6379"
echo "=========================================================="

${COMPOSE_CMD} up --build "$@"
