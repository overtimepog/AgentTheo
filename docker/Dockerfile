# Use Node.js 20 with Debian Bookworm as base
FROM node:20-bookworm

# Prevent interactive prompts
ENV DEBIAN_FRONTEND=noninteractive

# Set working directory
WORKDIR /app

# Install required packages, Python, pip, Playwright deps, and desktop environment
RUN apt-get update && apt-get install -y \
    python3 python3-pip python3-venv \
    # Desktop environment components
    xvfb x11vnc fluxbox \
    novnc websockify \
    # Additional browser dependencies for GUI
    libnss3 libnspr4 libatk1.0-0 libatk-bridge2.0-0 libcups2 libdbus-1-3 \
    libdrm2 libxkbcommon0 libatspi2.0-0 libx11-6 libxcomposite1 libxdamage1 \
    libxext6 libxfixes3 libxrandr2 libgbm1 libxcb1 libxss1 libgtk-3-0 \
    libasound2 fonts-liberation libappindicator3-1 xdg-utils \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/*

# Install Playwright and all required browsers (done once as root to cache)
RUN npx -y playwright@1.48.0 install --with-deps chromium firefox webkit

# Create Python virtual environment and activate it
RUN python3 -m venv /app/venv
ENV PATH="/app/venv/bin:$PATH"

# Pre-install Python dependencies separately to cache layer unless they change
COPY requirements.txt .
RUN pip install --upgrade pip && pip install -r requirements.txt

# Copy source code
COPY agent/ /app/agent/
COPY entrypoint.py /app/
COPY docker-entrypoint.sh /app/

# Set environment variables for desktop mode
ENV PYTHONUNBUFFERED=1 \
    PLAYWRIGHT_BROWSERS_PATH=/app/ms-playwright \
    PYTHONPATH=/app:$PYTHONPATH \
    DISPLAY=:1 \
    DEBIAN_FRONTEND=noninteractive

# Create and switch to non-root user
RUN groupadd -r agent && useradd -r -g agent agent \
    && chown -R agent:agent /app \
    && chmod +x /app/docker-entrypoint.sh

USER agent

# Install Playwright browser as non-root
RUN python -m playwright install chromium

# Expose VNC and noVNC ports
EXPOSE 5901 6080

# Entrypoint
ENTRYPOINT ["/app/docker-entrypoint.sh"]