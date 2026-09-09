#!/usr/bin/env bash
# ==============================================================================
# CropHealthAI - Automated Deployment Script
# Builds Docker images, pushes to Container Registry (Docker Hub / ECR / ACR),
# and deploys to Kubernetes, AWS ECS, or Azure App Service.
# ==============================================================================

set -eo pipefail

# Default configuration
REGISTRY="${REGISTRY:-docker.io/crophealth}"
TAG="${TAG:-$(git rev-parse --short HEAD 2>/dev/null || echo 'latest')}"
TARGET="${TARGET:-k8s}"           # Options: k8s, ecs, azure, all
ENVIRONMENT="${ENVIRONMENT:-production}"
SKIP_TESTS="${SKIP_TESTS:-false}"
K8S_NAMESPACE="${K8S_NAMESPACE:-crophealth}"

# Formatting
GREEN='\033[0;32m'
BLUE='\033[0;34m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m'

log_info() { echo -e "${BLUE}[INFO]${NC} $1"; }
log_success() { echo -e "${GREEN}[SUCCESS]${NC} $1"; }
log_warn() { echo -e "${YELLOW}[WARN]${NC} $1"; }
log_error() { echo -e "${RED}[ERROR]${NC} $1"; }

usage() {
    cat << EOF
Usage: $(basename "$0") [OPTIONS]

Options:
  -r, --registry <name>     Container registry prefix (default: docker.io/crophealth)
  -t, --tag <tag>           Image tag (default: git commit short SHA or 'latest')
  -d, --target <target>     Deployment target: 'k8s', 'ecs', 'azure' (default: k8s)
  -e, --env <env>           Environment: 'staging', 'production' (default: production)
  -s, --skip-tests          Skip pre-deployment tests
  -h, --help                Show this help message

Examples:
  ./scripts/deploy.sh --target k8s --tag v1.0.0
  ./scripts/deploy.sh --target ecs --registry 123456789.dkr.ecr.us-east-1.amazonaws.com
  ./scripts/deploy.sh --target azure --registry crophealthcr.azurecr.io
EOF
    exit 1
}

# Parse CLI arguments
while [[ "$#" -gt 0 ]]; do
    case "$1" in
        -r|--registry) REGISTRY="$2"; shift 2 ;;
        -t|--tag) TAG="$2"; shift 2 ;;
        -d|--target) TARGET="$2"; shift 2 ;;
        -e|--env) ENVIRONMENT="$2"; shift 2 ;;
        -s|--skip-tests) SKIP_TESTS="true"; shift 1 ;;
        -h|--help) usage ;;
        *) log_error "Unknown argument: $1"; usage ;;
    esac
done

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
ROOT_DIR="$(cd "${SCRIPT_DIR}/.." && pwd)"
cd "${ROOT_DIR}"

echo "=========================================================="
echo "  🌿 CropHealthAI Deployment Pipeline"
echo "  Registry:    ${REGISTRY}"
echo "  Image Tag:   ${TAG}"
echo "  Target:      ${TARGET}"
echo "  Environment: ${ENVIRONMENT}"
echo "=========================================================="

# ------------------------------------------------------------------------------
# 1. Pre-deployment Quality Gate
# ------------------------------------------------------------------------------
if [ "${SKIP_TESTS}" != "true" ]; then
    log_info "Running backend test suite before packaging..."
    if command -v pytest &> /dev/null; then
        python -m pytest backend/tests/test_auth.py backend/tests/test_reports.py -q
        log_success "Backend tests passed."
    else
        log_warn "pytest not found in current environment, skipping backend tests."
    fi

    if [ -d "frontend" ] && command -v npm &> /dev/null; then
        log_info "Running frontend tests and build check..."
        (cd frontend && npm test -- --watchAll=false --bail && npm run build)
        log_success "Frontend tests and build passed."
    fi
else
    log_warn "Skipping pre-deployment tests (--skip-tests active)."
fi

# ------------------------------------------------------------------------------
# 2. Build Docker Images
# ------------------------------------------------------------------------------
BACKEND_IMAGE="${REGISTRY}/crophealth-backend:${TAG}"
FRONTEND_IMAGE="${REGISTRY}/crophealth-frontend:${TAG}"

log_info "Building backend Docker image: ${BACKEND_IMAGE}..."
docker build -t "${BACKEND_IMAGE}" -t "${REGISTRY}/crophealth-backend:latest" -f backend/Dockerfile .

log_info "Building frontend Docker image: ${FRONTEND_IMAGE}..."
docker build -t "${FRONTEND_IMAGE}" -t "${REGISTRY}/crophealth-frontend:latest" -f frontend/Dockerfile ./frontend

log_success "Docker images built successfully."

# ------------------------------------------------------------------------------
# 3. Push Docker Images to Container Registry
# ------------------------------------------------------------------------------
log_info "Pushing backend image to ${REGISTRY}..."
docker push "${BACKEND_IMAGE}"
docker push "${REGISTRY}/crophealth-backend:latest"

log_info "Pushing frontend image to ${REGISTRY}..."
docker push "${FRONTEND_IMAGE}"
docker push "${REGISTRY}/crophealth-frontend:latest"

log_success "Container images pushed to registry."

# ------------------------------------------------------------------------------
# 4. Target Deployment Execution
# ------------------------------------------------------------------------------
case "${TARGET}" in
    k8s|kubernetes)
        log_info "Deploying to Kubernetes (Namespace: ${K8S_NAMESPACE})..."
        if ! command -v kubectl &> /dev/null; then
            log_error "kubectl is not installed or not in PATH."
            exit 1
        fi

        # Ensure namespace exists
        kubectl create namespace "${K8S_NAMESPACE}" --dry-run=client -o yaml | kubectl apply -f -

        # Apply configuration & secrets
        if [ -f "k8s/configmap.yaml" ]; then
            kubectl apply -f k8s/configmap.yaml -n "${K8S_NAMESPACE}"
        fi

        if [ -f "k8s/secrets.yaml" ]; then
            kubectl apply -f k8s/secrets.yaml -n "${K8S_NAMESPACE}"
        elif [ -f "k8s/secrets.template.yaml" ]; then
            log_warn "k8s/secrets.yaml not found. Applying secrets.template.yaml (Ensure production secrets are provisioned!)"
            kubectl apply -f k8s/secrets.template.yaml -n "${K8S_NAMESPACE}"
        fi

        # Apply workloads and services
        kubectl apply -f k8s/backend-deployment.yaml -n "${K8S_NAMESPACE}"
        kubectl apply -f k8s/backend-service.yaml -n "${K8S_NAMESPACE}"
        kubectl apply -f k8s/frontend-deployment.yaml -n "${K8S_NAMESPACE}"
        kubectl apply -f k8s/frontend-service.yaml -n "${K8S_NAMESPACE}"
        
        if [ -f "k8s/ingress.yaml" ]; then
            kubectl apply -f k8s/ingress.yaml -n "${K8S_NAMESPACE}"
        fi

        # Set specific image tag
        log_info "Updating container deployment images in cluster..."
        kubectl set image deployment/crophealth-backend backend="${BACKEND_IMAGE}" -n "${K8S_NAMESPACE}" --record || true
        kubectl set image deployment/crophealth-frontend frontend="${FRONTEND_IMAGE}" -n "${K8S_NAMESPACE}" --record || true

        log_info "Awaiting rollout status..."
        kubectl rollout status deployment/crophealth-backend -n "${K8S_NAMESPACE}" --timeout=180s
        kubectl rollout status deployment/crophealth-frontend -n "${K8S_NAMESPACE}" --timeout=120s
        log_success "Kubernetes deployment complete!"
        ;;

    ecs|aws)
        log_info "Deploying to AWS ECS..."
        if ! command -v aws &> /dev/null; then
            log_error "AWS CLI ('aws') is required for ECS deployment."
            exit 1
        fi

        CLUSTER_NAME="${AWS_ECS_CLUSTER:-crophealth-cluster}"
        BACKEND_SERVICE="${AWS_BACKEND_SERVICE:-crophealth-backend-service}"
        FRONTEND_SERVICE="${AWS_FRONTEND_SERVICE:-crophealth-frontend-service}"

        log_info "Triggering rolling deployment on ECS cluster: ${CLUSTER_NAME}"
        aws ecs update-service --cluster "${CLUSTER_NAME}" --service "${BACKEND_SERVICE}" --force-new-deployment
        aws ecs update-service --cluster "${CLUSTER_NAME}" --service "${FRONTEND_SERVICE}" --force-new-deployment
        log_success "AWS ECS deployment triggered successfully."
        ;;

    azure|appservice)
        log_info "Deploying to Azure App Service / Container Apps..."
        if ! command -v az &> /dev/null; then
            log_error "Azure CLI ('az') is required for Azure deployment."
            exit 1
        fi

        RESOURCE_GROUP="${AZ_RESOURCE_GROUP:-crophealth-rg}"
        BACKEND_APP="${AZ_BACKEND_APP:-crophealth-backend-app}"
        FRONTEND_APP="${AZ_FRONTEND_APP:-crophealth-frontend-app}"

        log_info "Updating Azure App Service container images..."
        az webapp config container set \
            --name "${BACKEND_APP}" \
            --resource-group "${RESOURCE_GROUP}" \
            --docker-custom-image-name "${BACKEND_IMAGE}"

        az webapp config container set \
            --name "${FRONTEND_APP}" \
            --resource-group "${RESOURCE_GROUP}" \
            --docker-custom-image-name "${FRONTEND_IMAGE}"

        log_success "Azure App Service updated successfully."
        ;;

    *)
        log_error "Unknown target '${TARGET}'. Supported targets: 'k8s', 'ecs', 'azure'."
        exit 1
        ;;
esac

echo "=========================================================="
log_success "Deployment process completed successfully!"
echo "=========================================================="
