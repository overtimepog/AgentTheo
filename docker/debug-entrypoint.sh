#!/bin/bash
set -e

echo "Starting Browser Agent in Debug Mode..."

# Start X virtual framebuffer
echo "Starting Xvfb..."
Xvfb :1 -screen 0 1280x720x24 &
XVFB_PID=$!

# Wait for Xvfb to start
sleep 2

# Export display
export DISPLAY=:1

# Start fluxbox window manager
echo "Starting window manager..."
fluxbox &

# Start VNC server
echo "Starting VNC server..."
x11vnc -display :1 -nopw -forever -shared -rfbport 5901 &

# Start noVNC web server
echo "Starting noVNC web interface..."
websockify -D --web=/usr/share/novnc/ 6080 localhost:5901

echo ""
echo "Desktop environment ready!"
echo "  - VNC: vnc://localhost:5901 (no password)"
echo "  - Web: http://localhost:6080/vnc.html"
echo ""

# Set container flag
export CONTAINER=docker

# Add debug environment variables
export LANGCHAIN_VERBOSE=true
export LANGCHAIN_TRACING_V2=false
export LOG_LEVEL=DEBUG

echo "Environment variables:"
echo "  - CONTAINER=$CONTAINER"
echo "  - LLM_MODEL=$LLM_MODEL"
echo "  - LOG_LEVEL=$LOG_LEVEL"
echo "  - TASK_DESCRIPTION=$TASK_DESCRIPTION"
echo ""

# Run the debug script instead of normal entrypoint
if [ "$DEBUG_MODE" = "true" ]; then
    echo "Running in DEBUG mode..."
    exec python /app/debug_container_issue.py --container
else
    echo "Running normal entrypoint..."
    exec python /app/entrypoint.py
fi