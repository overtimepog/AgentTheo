#!/bin/bash

# AgentTheo CLI - Web UI Mode
# Usage: ./run.sh [start|stop|restart|logs]

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
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
    echo -e "${BLUE}AgentTheo - Browser Automation with Web UI${NC}"
    echo ""
    echo "Usage:"
    echo "  $0 start               - Start AgentTheo with Web UI"
    echo "  $0 stop                - Stop AgentTheo"
    echo "  $0 restart             - Restart AgentTheo (rebuild if needed)"
    echo "  $0 restart -dev        - Quick restart (only rebuild app code)"
    echo "  $0 restart -hot        - Hot reload mode (instant code updates)"
    echo "  $0 restart --rebuild   - Force complete rebuild"
    echo "  $0 logs                - View AgentTheo logs"
    echo "  $0 status              - Check AgentTheo status"
    echo ""
    echo "Development flags:"
    echo "  -dev, --dev     - Fast rebuild, only updates application code"
    echo "  -hot, --hot     - Hot reload with volume mounts (no rebuild needed)"
    echo "  --rebuild       - Force complete rebuild with no cache"
    echo ""
    echo "Once started, access the Web UI at:"
    echo "  ${GREEN}http://localhost:8000${NC}"
    echo ""
    exit 1
}

# Function to check container status
check_status() {
    if docker ps --format '{{.Names}}' | grep -q '^agenttheo$'; then
        echo -e "${GREEN}AgentTheo is running${NC}"
        echo ""
        echo "Access points:"
        echo "  - Web UI: ${GREEN}http://localhost:8000${NC}"
        echo "  - VNC Viewer: http://localhost:6080/vnc.html"
        echo "  - VNC Direct: vnc://localhost:5901"
        return 0
    else
        echo -e "${YELLOW}AgentTheo is not running${NC}"
        return 1
    fi
}

# Function to start container
start_container() {
    # Check if already running
    if docker ps --format '{{.Names}}' | grep -q '^agenttheo$'; then
        echo -e "${YELLOW}AgentTheo is already running${NC}"
        check_status
        exit 0
    fi
    
    # Check if .env file exists
    if [ ! -f "config/.env" ]; then
        echo -e "${YELLOW}Warning: config/.env not found${NC}"
        echo "Creating from template..."
        cp config/.env.template config/.env
        echo -e "${RED}Please edit config/.env and add your OpenRouter API key${NC}"
        exit 1
    fi
    
    # Check if image exists
    if [[ "$(docker images -q agenttheo:latest 2> /dev/null)" == "" ]]; then
        echo -e "${GREEN}Building Docker image for first time...${NC}"
        echo -e "${BLUE}Using optimized multi-stage build${NC}"
        docker-compose -f docker/docker-compose.yml build
    fi
    
    echo -e "${GREEN}Starting AgentTheo...${NC}"
    
    # Start using docker-compose
    docker-compose -f docker/docker-compose.yml up -d
    
    # Wait for services to start
    echo -e "${YELLOW}Waiting for services to start...${NC}"
    sleep 5
    
    # Check if container is running
    if docker ps --format '{{.Names}}' | grep -q '^agenttheo$'; then
        echo ""
        echo -e "${GREEN}AgentTheo started successfully!${NC}"
        echo ""
        echo -e "${BLUE}Access the Web UI at:${NC}"
        echo -e "  ${GREEN}http://localhost:8000${NC}"
        echo ""
        echo "Other access points:"
        echo "  - VNC Viewer: http://localhost:6080/vnc.html"
        echo "  - VNC Direct: vnc://localhost:5901"
        echo ""
        echo -e "${YELLOW}Commands:${NC}"
        echo "  View logs: $0 logs"
        echo "  Stop: $0 stop"
        echo "  Check status: $0 status"
    else
        echo -e "${RED}Failed to start AgentTheo${NC}"
        echo "Check logs with: docker logs agenttheo"
        exit 1
    fi
}

# Function to stop container
stop_container() {
    echo -e "${YELLOW}Stopping AgentTheo...${NC}"
    # Try both compose files to ensure we stop any running instance
    docker-compose -f docker/docker-compose.yml down 2>/dev/null || true
    docker-compose -f docker/docker-compose.dev.yml down 2>/dev/null || true
    echo -e "${GREEN}AgentTheo stopped${NC}"
}

# Function to restart container
restart_container() {
    echo -e "${YELLOW}Restarting AgentTheo...${NC}"
    
    # Stop existing containers
    stop_container
    
    # Check flags
    if [ "$2" == "-dev" ] || [ "$2" == "--dev" ]; then
        echo -e "${GREEN}Dev mode: Quick rebuild of application code only...${NC}"
        echo -e "${BLUE}This skips dependency updates for faster testing${NC}"
        
        # Create a temporary Dockerfile for dev builds
        cat > docker/Dockerfile.dev <<EOF
# Dev-only Dockerfile that reuses existing layers
FROM agenttheo:latest

# Only copy application code
COPY --chown=agent:agent agent/ /app/agent/
COPY --chown=agent:agent entrypoint.py /app/
COPY --chown=agent:agent webui/ /app/webui/

# Ensure permissions are correct
RUN chmod +x /app/docker-entrypoint.sh
EOF
        
        # Build using dev Dockerfile
        docker build -t agenttheo:latest -f docker/Dockerfile.dev .
        
        # Clean up temp file
        rm docker/Dockerfile.dev
        
    elif [ "$2" == "-hot" ] || [ "$2" == "--hot" ]; then
        echo -e "${GREEN}Hot reload mode: Using volume mounts for instant code updates${NC}"
        echo -e "${BLUE}Code changes will be reflected immediately without rebuild${NC}"
        echo -e "${YELLOW}Note: Dependency changes still require full rebuild${NC}"
        
        # Use development docker-compose with volume mounts
        docker-compose -f docker/docker-compose.dev.yml up -d
        
        # Skip the normal start_container function
        echo ""
        echo -e "${GREEN}AgentTheo started in hot reload mode!${NC}"
        echo ""
        echo -e "${BLUE}Access the Web UI at:${NC}"
        echo -e "  ${GREEN}http://localhost:8000${NC}"
        echo ""
        echo "Other access points:"
        echo "  - VNC Viewer: http://localhost:6080/vnc.html"
        echo "  - VNC Direct: vnc://localhost:5901"
        echo ""
        echo -e "${YELLOW}Commands:${NC}"
        echo "  View logs: $0 logs"
        echo "  Stop: $0 stop"
        echo "  Check status: $0 status"
        return
        
    elif [ "$2" == "--rebuild" ] || [ ! -z "$(git status --porcelain 2>/dev/null)" ]; then
        echo -e "${GREEN}Rebuilding Docker image with latest changes...${NC}"
        
        # Remove the existing image to force complete rebuild
        if [[ "$(docker images -q agenttheo:latest 2> /dev/null)" != "" ]]; then
            echo -e "${GREEN}Removing existing image...${NC}"
            docker rmi agenttheo:latest
        fi
        
        # Build with no cache
        echo -e "${BLUE}Using optimized multi-stage build${NC}"
        docker-compose -f docker/docker-compose.yml build --no-cache
    else
        # Regular restart - rebuild if needed with cache
        echo -e "${BLUE}Using optimized multi-stage build${NC}"
        docker-compose -f docker/docker-compose.yml build
    fi
    
    # Start container
    start_container
}

# Function to view logs
view_logs() {
    if ! docker ps --format '{{.Names}}' | grep -q '^agenttheo$'; then
        echo -e "${YELLOW}AgentTheo is not running${NC}"
        exit 1
    fi
    
    echo -e "${GREEN}Viewing AgentTheo logs...${NC}"
    echo -e "${YELLOW}Press Ctrl+C to exit${NC}"
    echo ""
    docker logs -f agenttheo
}

# Check arguments
if [ "$#" -lt 1 ]; then
    usage
fi

# Handle commands
case "$1" in
    start)
        start_container
        ;;
    stop)
        stop_container
        ;;
    restart)
        restart_container "$@"
        ;;
    logs)
        view_logs
        ;;
    status)
        check_status
        ;;
    *)
        usage
        ;;
esac