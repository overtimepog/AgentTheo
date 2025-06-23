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
    echo "  $0 start      - Start AgentTheo with Web UI"
    echo "  $0 stop       - Stop AgentTheo"
    echo "  $0 restart    - Restart AgentTheo (rebuild if needed)"
    echo "  $0 logs       - View AgentTheo logs"
    echo "  $0 status     - Check AgentTheo status"
    echo ""
    echo "Once started, access the Web UI at:"
    echo "  ${GREEN}http://localhost:8000${NC}"
    echo ""
    exit 1
}

# Function to check container status
check_status() {
    if docker ps --format '{{.Names}}' | grep -q '^browser-agent$'; then
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
    if docker ps --format '{{.Names}}' | grep -q '^browser-agent$'; then
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
    if [[ "$(docker images -q browser-agent:latest 2> /dev/null)" == "" ]]; then
        echo -e "${GREEN}Building Docker image for first time...${NC}"
        docker-compose -f docker/docker-compose.yml build
    fi
    
    echo -e "${GREEN}Starting AgentTheo...${NC}"
    
    # Start using docker-compose
    docker-compose -f docker/docker-compose.yml up -d
    
    # Wait for services to start
    echo -e "${YELLOW}Waiting for services to start...${NC}"
    sleep 5
    
    # Check if container is running
    if docker ps --format '{{.Names}}' | grep -q '^browser-agent$'; then
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
        echo "Check logs with: docker logs browser-agent"
        exit 1
    fi
}

# Function to stop container
stop_container() {
    echo -e "${YELLOW}Stopping AgentTheo...${NC}"
    docker-compose -f docker/docker-compose.yml down
    echo -e "${GREEN}AgentTheo stopped${NC}"
}

# Function to restart container
restart_container() {
    echo -e "${YELLOW}Restarting AgentTheo...${NC}"
    
    # Stop existing containers
    stop_container
    
    # Check if rebuild is requested or if code has changed
    if [ "$2" == "--rebuild" ] || [ ! -z "$(git status --porcelain 2>/dev/null)" ]; then
        echo -e "${GREEN}Rebuilding Docker image with latest changes...${NC}"
        
        # Remove the existing image to force complete rebuild
        if [[ "$(docker images -q browser-agent:latest 2> /dev/null)" != "" ]]; then
            echo -e "${GREEN}Removing existing image...${NC}"
            docker rmi browser-agent:latest
        fi
        
        # Build with no cache
        docker-compose -f docker/docker-compose.yml build --no-cache
    fi
    
    # Start container
    start_container
}

# Function to view logs
view_logs() {
    if ! docker ps --format '{{.Names}}' | grep -q '^browser-agent$'; then
        echo -e "${YELLOW}AgentTheo is not running${NC}"
        exit 1
    fi
    
    echo -e "${GREEN}Viewing AgentTheo logs...${NC}"
    echo -e "${YELLOW}Press Ctrl+C to exit${NC}"
    echo ""
    docker logs -f browser-agent
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