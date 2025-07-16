#!/bin/bash

# NFT-Gated AI Trading Bot Deployment Script
# Usage: ./scripts/deploy.sh [environment] [options]

set -e

# Default values
ENVIRONMENT="development"
BUILD_IMAGE=false
PUSH_IMAGE=false
RUN_MIGRATIONS=true
RUN_TESTS=false
DOCKER_REGISTRY=""
IMAGE_TAG="latest"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Logging functions
log_info() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

log_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

log_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

log_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# Help function
show_help() {
    cat << EOF
NFT-Gated AI Trading Bot Deployment Script

Usage: $0 [ENVIRONMENT] [OPTIONS]

ENVIRONMENTS:
    development     Deploy to local development environment
    staging         Deploy to staging environment
    production      Deploy to production environment

OPTIONS:
    -b, --build         Build Docker image
    -p, --push          Push Docker image to registry
    -t, --tag TAG       Docker image tag (default: latest)
    -r, --registry URL  Docker registry URL
    --no-migrations     Skip database migrations
    --run-tests         Run tests before deployment
    -h, --help          Show this help message

EXAMPLES:
    $0 development
    $0 staging --build --push --tag v1.2.3
    $0 production --registry myregistry.com --tag v1.2.3 --run-tests

ENVIRONMENT VARIABLES:
    DOCKER_USERNAME     Docker registry username
    DOCKER_PASSWORD     Docker registry password
    DATABASE_URL        Database connection string
    REDIS_URL          Redis connection string
    SECRET_KEY         Application secret key
EOF
}

# Parse command line arguments
parse_args() {
    while [[ $# -gt 0 ]]; do
        case $1 in
            development|staging|production)
                ENVIRONMENT="$1"
                shift
                ;;
            -b|--build)
                BUILD_IMAGE=true
                shift
                ;;
            -p|--push)
                PUSH_IMAGE=true
                shift
                ;;
            -t|--tag)
                IMAGE_TAG="$2"
                shift 2
                ;;
            -r|--registry)
                DOCKER_REGISTRY="$2"
                shift 2
                ;;
            --no-migrations)
                RUN_MIGRATIONS=false
                shift
                ;;
            --run-tests)
                RUN_TESTS=true
                shift
                ;;
            -h|--help)
                show_help
                exit 0
                ;;
            *)
                log_error "Unknown option: $1"
                show_help
                exit 1
                ;;
        esac
    done
}

# Check prerequisites
check_prerequisites() {
    log_info "Checking prerequisites..."
    
    # Check if Docker is installed
    if ! command -v docker &> /dev/null; then
        log_error "Docker is not installed"
        exit 1
    fi
    
    # Check if Docker Compose is installed
    if ! command -v docker-compose &> /dev/null; then
        log_error "Docker Compose is not installed"
        exit 1
    fi
    
    # Check if required environment files exist
    if [[ ! -f ".env.${ENVIRONMENT}" ]]; then
        log_warning "Environment file .env.${ENVIRONMENT} not found"
        if [[ ! -f ".env" ]]; then
            log_error "No environment file found. Please create .env or .env.${ENVIRONMENT}"
            exit 1
        fi
    fi
    
    log_success "Prerequisites check passed"
}

# Load environment variables
load_environment() {
    log_info "Loading environment variables for ${ENVIRONMENT}..."
    
    # Load environment-specific file first
    if [[ -f ".env.${ENVIRONMENT}" ]]; then
        export $(cat .env.${ENVIRONMENT} | grep -v '^#' | xargs)
        log_info "Loaded .env.${ENVIRONMENT}"
    elif [[ -f ".env" ]]; then
        export $(cat .env | grep -v '^#' | xargs)
        log_info "Loaded .env"
    fi
    
    # Set deployment-specific variables
    export ENVIRONMENT
    export IMAGE_TAG
    
    if [[ -n "$DOCKER_REGISTRY" ]]; then
        export DOCKER_REGISTRY
    fi
}

# Run tests
run_tests() {
    if [[ "$RUN_TESTS" == true ]]; then
        log_info "Running tests..."
        
        # Install test dependencies
        pip install -r requirements.txt
        pip install pytest pytest-cov pytest-asyncio
        
        # Run unit tests
        pytest tests/unit/ -v --cov=api --cov=core --cov=integrations
        
        # Run integration tests (excluding external services)
        pytest tests/integration/ -v -m "not external"
        
        log_success "Tests passed"
    fi
}

# Build Docker image
build_image() {
    if [[ "$BUILD_IMAGE" == true ]]; then
        log_info "Building Docker image..."
        
        local image_name="nft-trading-bot"
        if [[ -n "$DOCKER_REGISTRY" ]]; then
            image_name="${DOCKER_REGISTRY}/${image_name}"
        fi
        
        docker build -t "${image_name}:${IMAGE_TAG}" .
        
        # Also tag as latest for local development
        if [[ "$ENVIRONMENT" == "development" ]]; then
            docker tag "${image_name}:${IMAGE_TAG}" "${image_name}:latest"
        fi
        
        log_success "Docker image built: ${image_name}:${IMAGE_TAG}"
    fi
}

# Push Docker image
push_image() {
    if [[ "$PUSH_IMAGE" == true ]]; then
        log_info "Pushing Docker image..."
        
        if [[ -z "$DOCKER_REGISTRY" ]]; then
            log_error "Docker registry not specified. Use --registry option."
            exit 1
        fi
        
        # Login to Docker registry if credentials are provided
        if [[ -n "$DOCKER_USERNAME" && -n "$DOCKER_PASSWORD" ]]; then
            echo "$DOCKER_PASSWORD" | docker login "$DOCKER_REGISTRY" -u "$DOCKER_USERNAME" --password-stdin
        fi
        
        local image_name="${DOCKER_REGISTRY}/nft-trading-bot"
        docker push "${image_name}:${IMAGE_TAG}"
        
        log_success "Docker image pushed: ${image_name}:${IMAGE_TAG}"
    fi
}

# Run database migrations
run_migrations() {
    if [[ "$RUN_MIGRATIONS" == true ]]; then
        log_info "Running database migrations..."
        
        case $ENVIRONMENT in
            development)
                # For development, use docker-compose
                docker-compose exec api python -m alembic upgrade head
                ;;
            staging|production)
                # For staging/production, run migrations in a temporary container
                docker run --rm \
                    --env-file ".env.${ENVIRONMENT}" \
                    --network host \
                    "nft-trading-bot:${IMAGE_TAG}" \
                    python -m alembic upgrade head
                ;;
        esac
        
        log_success "Database migrations completed"
    fi
}

# Deploy to development
deploy_development() {
    log_info "Deploying to development environment..."
    
    # Stop existing containers
    docker-compose down
    
    # Start services
    docker-compose up -d
    
    # Wait for services to be ready
    log_info "Waiting for services to be ready..."
    sleep 10
    
    # Check health
    if curl -f http://localhost:8000/health/ > /dev/null 2>&1; then
        log_success "Development deployment successful"
        log_info "API available at: http://localhost:8000"
        log_info "Flower (Celery monitoring) available at: http://localhost:5555"
    else
        log_error "Development deployment failed - health check failed"
        exit 1
    fi
}

# Deploy to staging
deploy_staging() {
    log_info "Deploying to staging environment..."
    
    # This would typically involve:
    # - Updating Kubernetes manifests
    # - Applying configuration changes
    # - Rolling out new version
    
    log_warning "Staging deployment not fully implemented"
    log_info "Would deploy image: nft-trading-bot:${IMAGE_TAG}"
}

# Deploy to production
deploy_production() {
    log_info "Deploying to production environment..."
    
    # Production deployment safety checks
    if [[ "$IMAGE_TAG" == "latest" ]]; then
        log_error "Cannot deploy 'latest' tag to production. Use a specific version tag."
        exit 1
    fi
    
    # This would typically involve:
    # - Blue-green deployment
    # - Health checks
    # - Rollback capability
    
    log_warning "Production deployment not fully implemented"
    log_info "Would deploy image: nft-trading-bot:${IMAGE_TAG}"
}

# Main deployment function
deploy() {
    case $ENVIRONMENT in
        development)
            deploy_development
            ;;
        staging)
            deploy_staging
            ;;
        production)
            deploy_production
            ;;
        *)
            log_error "Unknown environment: $ENVIRONMENT"
            exit 1
            ;;
    esac
}

# Cleanup function
cleanup() {
    log_info "Cleaning up..."
    
    # Remove old Docker images (keep last 3 versions)
    docker images "nft-trading-bot" --format "table {{.Repository}}:{{.Tag}}\t{{.CreatedAt}}" | \
        tail -n +4 | \
        awk '{print $1}' | \
        xargs -r docker rmi || true
    
    log_success "Cleanup completed"
}

# Main execution
main() {
    log_info "Starting deployment process..."
    log_info "Environment: $ENVIRONMENT"
    log_info "Image tag: $IMAGE_TAG"
    
    parse_args "$@"
    check_prerequisites
    load_environment
    run_tests
    build_image
    push_image
    run_migrations
    deploy
    cleanup
    
    log_success "Deployment completed successfully!"
}

# Run main function with all arguments
main "$@"

