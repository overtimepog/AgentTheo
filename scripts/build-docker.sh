#!/bin/bash
# Optimized Docker build script with BuildKit

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Default values
BROWSER="${BROWSER:-chromium}"
PYTHON_VERSION="${PYTHON_VERSION:-3.11}"
NODE_VERSION="${NODE_VERSION:-20}"
DOCKER_BUILDKIT=1

# Help function
show_help() {
    echo "Usage: $0 [OPTIONS]"
    echo ""
    echo "Options:"
    echo "  -b, --browser BROWSER     Browser to install (chromium|firefox|webkit) [default: chromium]"
    echo "  -p, --python VERSION      Python version [default: 3.11]"
    echo "  -n, --node VERSION        Node version [default: 20]"
    echo "  --no-cache               Build without cache"
    echo "  --push                   Push image after build"
    echo "  -h, --help               Show this help message"
    echo ""
    echo "Examples:"
    echo "  $0                       # Build with defaults"
    echo "  $0 -b firefox            # Build with Firefox"
    echo "  $0 --no-cache            # Fresh build"
}

# Parse arguments
CACHE_OPTION=""
PUSH_IMAGE=false

while [[ $# -gt 0 ]]; do
    case $1 in
        -b|--browser)
            BROWSER="$2"
            shift 2
            ;;
        -p|--python)
            PYTHON_VERSION="$2"
            shift 2
            ;;
        -n|--node)
            NODE_VERSION="$2"
            shift 2
            ;;
        --no-cache)
            CACHE_OPTION="--no-cache"
            shift
            ;;
        --push)
            PUSH_IMAGE=true
            shift
            ;;
        -h|--help)
            show_help
            exit 0
            ;;
        *)
            echo -e "${RED}Unknown option: $1${NC}"
            show_help
            exit 1
            ;;
    esac
done

# Validate browser choice
if [[ ! "$BROWSER" =~ ^(chromium|firefox|webkit)$ ]]; then
    echo -e "${RED}Error: Invalid browser '$BROWSER'. Must be chromium, firefox, or webkit.${NC}"
    exit 1
fi

# Export BuildKit
export DOCKER_BUILDKIT=1
export COMPOSE_DOCKER_CLI_BUILD=1

echo -e "${GREEN}Building AgentTheo Docker image...${NC}"
echo -e "${YELLOW}Configuration:${NC}"
echo "  Browser: $BROWSER"
echo "  Python: $PYTHON_VERSION"
echo "  Node: $NODE_VERSION"
echo "  BuildKit: Enabled"
echo ""

# Change to project root
cd "$(dirname "$0")/.."

# Build with docker-compose
echo -e "${GREEN}Starting build...${NC}"
time docker-compose -f docker/docker-compose.yml build \
    --build-arg BROWSER=$BROWSER \
    --build-arg PYTHON_VERSION=$PYTHON_VERSION \
    --build-arg NODE_VERSION=$NODE_VERSION \
    $CACHE_OPTION \
    agenttheo

# Show image info
echo ""
echo -e "${GREEN}Build complete!${NC}"
docker images agenttheo:latest

# Push if requested
if [ "$PUSH_IMAGE" = true ]; then
    echo -e "${YELLOW}Pushing image...${NC}"
    docker push agenttheo:latest
fi

echo -e "${GREEN}Done!${NC}"

# Optional: Test the build
if [ -t 0 ]; then
    echo ""
    read -p "Would you like to test the build? (y/N) " -n 1 -r
    echo ""
    if [[ $REPLY =~ ^[Yy]$ ]]; then
        echo -e "${YELLOW}Testing health check...${NC}"
        docker run --rm -d --name agenttheo-test -p 8000:8000 agenttheo:latest
        sleep 5
        if curl -f http://localhost:8000/health >/dev/null 2>&1; then
            echo -e "${GREEN}✓ Health check passed!${NC}"
        else
            echo -e "${RED}✗ Health check failed!${NC}"
        fi
        docker stop agenttheo-test
    fi
fi