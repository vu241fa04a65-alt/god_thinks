#!/usr/bin/env bash
# ==============================================================================
# CropHealthAI - Terraform Managed Infrastructure Provisioning Stub
# Provisions Managed PostgreSQL (AWS RDS) and Leaf Image Storage (AWS S3)
# ==============================================================================

set -eo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
ROOT_DIR="$(cd "${SCRIPT_DIR}/.." && pwd)"
TF_DIR="${ROOT_DIR}/terraform"

ACTION="${1:-plan}"
ENV="${ENVIRONMENT:-production}"

# Colors
GREEN='\033[0;32m'
BLUE='\033[0;34m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m'

echo "=========================================================="
echo "  ☁️ CropHealthAI Infrastructure Provisioning"
echo "  Action:      ${ACTION}"
echo "  Environment: ${ENV}"
echo "  Terraform:   ${TF_DIR}"
echo "=========================================================="

# Check if terraform CLI is installed
if ! command -v terraform &> /dev/null; then
    echo -e "${YELLOW}[NOTICE] 'terraform' binary not detected in PATH.${NC}"
    echo "Running in infrastructure simulation mode (dry-run stub)..."
    echo ""
    echo "This stub demonstrates the provisioning of:"
    echo "  1. 🗄️  AWS RDS PostgreSQL 15 Instance (crophealth-${ENV}-pg)"
    echo "     - Engine: PostgreSQL 15.5"
    echo "     - Multi-AZ subnets, automated 7-day backups, encryption at rest (AES-256)"
    echo "     - Ingress restricted to application VPC"
    echo ""
    echo "  2. 🪣 AWS S3 Bucket (crophealth-${ENV}-leaf-storage-xxxx)"
    echo "     - Versioning enabled for image rollback"
    echo "     - Default server-side encryption"
    echo "     - CORS enabled for browser direct-upload / visual inspection"
    echo ""
    echo "Generated Mock Environment Output:"
    echo "----------------------------------------------------------"
    echo "DATABASE_URL=\"postgresql://crophealth_admin:secure_pass_gen@crophealth-${ENV}-pg.c8x2a.us-east-1.rds.amazonaws.com:5432/crophealth_db\""
    echo "S3_BUCKET_NAME=\"crophealth-${ENV}-leaf-storage-a8b2c1d4\""
    echo "AWS_REGION=\"us-east-1\""
    echo "----------------------------------------------------------"
    echo ""
    echo -e "${GREEN}To provision real cloud infrastructure:${NC}"
    echo "1. Install Terraform: https://developer.hashicorp.com/terraform/install"
    echo "2. Configure AWS CLI: aws configure"
    echo "3. Run: ./scripts/terraform_stub.sh apply"
    exit 0
fi

cd "${TF_DIR}"

case "${ACTION}" in
    init)
        echo -e "${BLUE}[INFO] Initializing Terraform providers and modules...${NC}"
        terraform init
        ;;
    plan)
        echo -e "${BLUE}[INFO] Generating infrastructure execution plan...${NC}"
        terraform init -upgrade
        terraform plan -var="environment=${ENV}"
        ;;
    apply)
        echo -e "${BLUE}[INFO] Applying infrastructure plan (Creating RDS & S3)...${NC}"
        terraform init
        terraform apply -var="environment=${ENV}" -auto-approve
        echo ""
        echo -e "${GREEN}[SUCCESS] Infrastructure provisioned successfully!${NC}"
        echo "Retrieving connection outputs:"
        terraform output
        ;;
    destroy)
        echo -e "${RED}[WARN] Destroying managed infrastructure...${NC}"
        terraform destroy -var="environment=${ENV}"
        ;;
    output)
        terraform output
        ;;
    *)
        echo -e "${RED}[ERROR] Unknown action '${ACTION}'. Supported: init, plan, apply, destroy, output.${NC}"
        exit 1
        ;;
esac
