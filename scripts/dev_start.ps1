# ==============================================================================
# CropHealthAI - Windows PowerShell Local Development Startup Script
# ==============================================================================

$ErrorActionPreference = "Stop"

$scriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
$rootDir = Split-Path -Parent $scriptDir

Set-Location $rootDir

Write-Host "==========================================================" -ForegroundColor Green
Write-Host "  🌿 Starting CropHealthAI Full Stack via Docker Compose" -ForegroundColor Green
Write-Host "==========================================================" -ForegroundColor Green

# 1. Check Docker
if (-not (Get-Command docker -ErrorAction SilentlyContinue)) {
    Write-Error "Docker is not installed or not in PATH."
    exit 1
}

# 2. Setup env files if missing
if (-not (Test-Path "backend\.env") -and (Test-Path "backend\.env.example")) {
    Write-Host "📋 Creating backend\.env from template..." -ForegroundColor Cyan
    Copy-Item "backend\.env.example" "backend\.env"
}

if (-not (Test-Path "frontend\.env") -and (Test-Path "frontend\.env.example")) {
    Write-Host "📋 Creating frontend\.env from template..." -ForegroundColor Cyan
    Copy-Item "frontend\.env.example" "frontend\.env"
}

# 3. Choose compose command
$composeCmd = "docker compose"
try {
    docker compose version | Out-Null
} catch {
    $composeCmd = "docker-compose"
}

Write-Host "🚀 Launching services..." -ForegroundColor Cyan
Write-Host "  - Frontend Web UI:  http://localhost:3000"
Write-Host "  - Backend API:      http://localhost:8000"
Write-Host "  - Swagger API Docs: http://localhost:8000/docs"
Write-Host "  - pgAdmin:          http://localhost:5050"
Write-Host "==========================================================" -ForegroundColor Green

& docker compose up --build $args
