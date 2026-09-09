# ==============================================================================
# CropHealthAI - Windows PowerShell Terraform Provisioning Stub
# ==============================================================================

param (
    [string]$Action = "plan",
    [string]$Environment = "production"
)

$scriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
$rootDir = Split-Path -Parent $scriptDir
$tfDir = Join-Path $rootDir "terraform"

Write-Host "==========================================================" -ForegroundColor Green
Write-Host "  ☁️ CropHealthAI Infrastructure Provisioning (PowerShell)" -ForegroundColor Green
Write-Host "  Action:      $Action" -ForegroundColor Cyan
Write-Host "  Environment: $Environment" -ForegroundColor Cyan
Write-Host "  Terraform:   $tfDir" -ForegroundColor Cyan
Write-Host "==========================================================" -ForegroundColor Green

if (-not (Get-Command terraform -ErrorAction SilentlyContinue)) {
    Write-Host "[NOTICE] 'terraform' CLI not detected in PATH. Running simulation mode..." -ForegroundColor Yellow
    Write-Host ""
    Write-Host "Managed Resources Simulated:"
    Write-Host "  1. AWS RDS PostgreSQL 15 Instance (crophealth-$Environment-pg)"
    Write-Host "  2. AWS S3 Bucket (crophealth-$Environment-leaf-storage-xxxx)"
    Write-Host ""
    Write-Host "Mock Generated Outputs:" -ForegroundColor Green
    Write-Host "DATABASE_URL=`"postgresql://crophealth_admin:secure_pass_gen@crophealth-$Environment-pg.c8x2a.us-east-1.rds.amazonaws.com:5432/crophealth_db`""
    Write-Host "S3_BUCKET_NAME=`"crophealth-$Environment-leaf-storage-a8b2c1d4`""
    Write-Host "AWS_REGION=`"us-east-1`""
    exit 0
}

Set-Location $tfDir

switch ($Action) {
    "init" { & terraform init }
    "plan" { & terraform plan -var="environment=$Environment" }
    "apply" { & terraform apply -var="environment=$Environment" -auto-approve }
    "destroy" { & terraform destroy -var="environment=$Environment" }
    "output" { & terraform output }
    default { Write-Error "Unknown action '$Action'" }
}
