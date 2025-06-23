#!/bin/bash

# Migration script to switch from old Dockerfile to optimized version

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

echo -e "${BLUE}AgentTheo Docker Optimization Migration${NC}"
echo ""
echo "This script will:"
echo "1. Stop any running AgentTheo containers"
echo "2. Remove the old Docker image"
echo "3. Build the new optimized image"
echo "4. Start AgentTheo with the optimized image"
echo ""
read -p "Continue? [y/N] " -n 1 -r
echo ""

if [[ ! $REPLY =~ ^[Yy]$ ]]; then
    echo -e "${YELLOW}Migration cancelled${NC}"
    exit 0
fi

# Change to project root
cd "$(dirname "$0")/.."

# Step 1: Stop running containers
echo -e "${YELLOW}Stopping AgentTheo...${NC}"
docker-compose -f docker/docker-compose.yml down 2>/dev/null || true

# Step 2: Remove old image
if [[ "$(docker images -q agenttheo:latest 2> /dev/null)" != "" ]]; then
    echo -e "${YELLOW}Removing old Docker image...${NC}"
    docker rmi agenttheo:latest
fi

# Step 3: Build new optimized image
echo -e "${GREEN}Building optimized Docker image...${NC}"
echo -e "${BLUE}Using multi-stage build with BuildKit${NC}"
DOCKER_BUILDKIT=1 docker-compose -f docker/docker-compose.yml build

# Step 4: Show results
echo ""
echo -e "${GREEN}Migration completed successfully!${NC}"
echo ""
echo "Image size comparison:"
docker images agenttheo:latest --format "table {{.Repository}}\t{{.Tag}}\t{{.Size}}"
echo ""
echo -e "${BLUE}Start AgentTheo with:${NC} ./run.sh start"