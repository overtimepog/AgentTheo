#!/bin/bash

# Browser Agent CLI - Desktop Only Mode
# Usage: ./run.sh task "your natural language command"

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Script directory
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" &> /dev/null && pwd )"
cd "$SCRIPT_DIR"

# Check if Docker is installed
if ! command -v docker &> /dev/null; then
    echo -e "${RED}Error: Docker is not installed${NC}"
    exit 1
fi

# Check if Docker is running
if ! docker info &> /dev/null; then
    echo -e "${RED}Error: Docker daemon is not running${NC}"
    exit 1
fi

# Function to display usage
usage() {
    echo "Usage:"
    echo "  $0 task \"<natural language command>\"  - Run a browser automation task"
    echo "  $0 restart                             - Rebuild container with latest changes"
    echo ""
    echo "Examples:"
    echo "  $0 task \"go to google and search for AI news\""
    echo "  $0 restart"
    echo ""
    echo "Note: Browser will always run with GUI visible via VNC/noVNC"
    exit 1
}

# Function to rebuild container
restart_container() {
    echo -e "${YELLOW}Rebuilding browser agent with latest changes...${NC}"
    
    # Stop and remove existing containers
    echo -e "${GREEN}Stopping existing containers...${NC}"
    docker-compose -f docker/docker-compose.yml down
    docker stop browser-agent 2>/dev/null || true
    docker rm browser-agent 2>/dev/null || true
    
    # Remove the existing image to force complete rebuild
    if [[ "$(docker images -q browser-agent:latest 2> /dev/null)" != "" ]]; then
        echo -e "${GREEN}Removing existing image...${NC}"
        docker rmi browser-agent:latest
    fi
    
    # Build with no cache to ensure latest changes are included
    echo -e "${GREEN}Building fresh Docker image (this may take a few minutes)...${NC}"
    docker-compose -f docker/docker-compose.yml build --no-cache
    
    echo -e "${GREEN}Container rebuilt successfully!${NC}"
    echo -e "${YELLOW}You can now run tasks with: $0 task \"your command\"${NC}"
    exit 0
}

# Check arguments
if [ "$#" -lt 1 ]; then
    usage
fi

# Handle restart command
if [ "$1" == "restart" ]; then
    restart_container
fi

# Handle task command
if [ "$1" != "task" ]; then
    usage
fi

if [ "$#" -lt 2 ]; then
    usage
fi

TASK_DESCRIPTION="$2"

# Check if .env file exists
if [ ! -f "config/.env" ]; then
    echo -e "${YELLOW}Warning: config/.env not found${NC}"
    echo "Creating from template..."
    cp config/.env.template config/.env
    echo -e "${RED}Please edit config/.env and add your OpenRouter API key${NC}"
    exit 1
fi

# Check if image exists
if [[ "$(docker images -q browser-agent:latest 2> /dev/null)" == "" ]]; then
    echo -e "${GREEN}Building Docker image for first time...${NC}"
    docker-compose -f docker/docker-compose.yml build
else
    echo -e "${GREEN}Using existing Docker image...${NC}"
fi

# Run the task with desktop mode
echo -e "${GREEN}Starting browser agent with desktop environment...${NC}"
echo -e "${YELLOW}Task: $TASK_DESCRIPTION${NC}"
echo ""

# Stop any existing container
docker stop browser-agent 2>/dev/null || true
docker rm browser-agent 2>/dev/null || true

# Run in detached mode with ports exposed
docker run -d \
    --name browser-agent \
    -p 5901:5901 \
    -p 6080:6080 \
    -v "$(pwd)/logs:/app/logs" \
    -v "$(pwd)/config:/app/config:ro" \
    --env-file config/.env \
    -e "TASK_DESCRIPTION=$TASK_DESCRIPTION" \
    -e "LOG_LEVEL=${LOG_LEVEL:-INFO}" \
    -e "BROWSER=${BROWSER:-chromium}" \
    --cap-add SYS_ADMIN \
    --security-opt seccomp=unconfined \
    --shm-size=2gb \
    browser-agent:latest

echo ""
echo -e "${GREEN}Desktop environment started!${NC}"
echo -e "${YELLOW}Access the browser:${NC}"
echo "  - Web: http://localhost:6080/vnc.html"
echo "  - VNC: vnc://localhost:5901 (no password)"
echo ""
echo -e "${YELLOW}View logs:${NC} docker logs -f browser-agent"
echo -e "${YELLOW}Stop:${NC} docker stop browser-agent"
echo ""

# Follow logs
echo -e "${GREEN}Following logs...${NC}"
docker logs -f browser-agent