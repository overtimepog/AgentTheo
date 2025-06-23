#!/bin/bash
set -e

echo "Starting Browser Agent in Desktop Mode..."

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

# Start the web UI in the background
echo "Starting AgentTheo Web UI..."
python /app/webui.py &
WEB_UI_PID=$!

# Give the web UI time to start
sleep 2

echo ""
echo "AgentTheo Web UI ready!"
echo "  - Access the full interface at: http://localhost:8000"
echo ""

# Run the Python application
exec python /app/entrypoint.py