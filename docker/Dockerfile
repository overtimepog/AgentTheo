# syntax=docker/dockerfile:1.4
# Multi-stage optimized Dockerfile for AgentTheo with Playwright

# Build arguments
ARG PYTHON_VERSION=3.11
ARG NODE_VERSION=20
ARG BROWSER=chromium

# Stage 1: Builder stage for dependencies
FROM node:${NODE_VERSION}-bookworm as builder

ENV DEBIAN_FRONTEND=noninteractive
WORKDIR /app

# Install build dependencies and Python
RUN apt-get update && apt-get install -y --no-install-recommends \
    python3.11 python3.11-venv python3-pip \
    build-essential \
    && rm -rf /var/lib/apt/lists/*

# Create Python virtual environment
RUN python3.11 -m venv /app/venv
ENV PATH="/app/venv/bin:$PATH"

# Copy and install Python dependencies with cache mount
COPY requirements.txt .
RUN --mount=type=cache,target=/root/.cache/pip \
    pip install --upgrade pip && \
    pip install -r requirements.txt

# Install Playwright and specified browser only
ENV PLAYWRIGHT_BROWSERS_PATH=/ms-playwright
ARG BROWSER
RUN npx -y playwright@1.48.0 install --with-deps ${BROWSER}

# Stage 2: Runtime stage with minimal footprint
FROM node:${NODE_VERSION}-bookworm-slim

ARG PYTHON_VERSION=3.11
ENV DEBIAN_FRONTEND=noninteractive
WORKDIR /app

# Create user early for better layer caching
RUN groupadd -r agent && useradd -r -g agent -m agent && \
    mkdir -p /var/log/supervisor && \
    chown -R agent:agent /var/log/supervisor

# Install only runtime dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    python${PYTHON_VERSION} python${PYTHON_VERSION}-venv \
    # Desktop environment components
    xvfb x11vnc fluxbox \
    novnc websockify \
    # Process manager
    supervisor \
    # Healthcheck
    curl \
    # Browser runtime dependencies (minimal set)
    libnss3 libnspr4 libatk1.0-0 libatk-bridge2.0-0 libcups2 libdbus-1-3 \
    libdrm2 libxkbcommon0 libatspi2.0-0 libx11-6 libxcomposite1 libxdamage1 \
    libxext6 libxfixes3 libxrandr2 libgbm1 libxcb1 libxss1 libgtk-3-0 \
    libasound2 fonts-liberation libappindicator3-1 xdg-utils \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/*

# Copy Python virtual environment from builder
COPY --from=builder --chown=agent:agent /app/venv /app/venv
ENV PATH="/app/venv/bin:$PATH"

# Copy Playwright installation from builder
COPY --from=builder /ms-playwright /ms-playwright

# Copy application files
COPY --chown=agent:agent agent/ /app/agent/
COPY --chown=agent:agent entrypoint.py /app/
COPY --chown=agent:agent webui/ /app/webui/
COPY --chown=agent:agent docker/docker-entrypoint.sh /app/
COPY docker/supervisord.conf /etc/supervisor/conf.d/supervisord.conf

# Set executable permissions
RUN chmod +x /app/docker-entrypoint.sh

# Set environment variables
ENV PYTHONUNBUFFERED=1 \
    PLAYWRIGHT_BROWSERS_PATH=/ms-playwright \
    PYTHONPATH=/app:$PYTHONPATH \
    DISPLAY=:1

# Expose VNC and noVNC ports
EXPOSE 5901 6080 8000

# Healthcheck
HEALTHCHECK --interval=30s --timeout=10s --start-period=40s --retries=3 \
    CMD curl -f http://localhost:8000/health || exit 1

# Use supervisor as the main process
CMD ["/usr/bin/supervisord", "-c", "/etc/supervisor/conf.d/supervisord.conf"]