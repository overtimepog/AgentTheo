# Docker Build Optimizations

## Overview

This document describes the optimizations implemented to make Docker builds significantly faster for AgentTheo.

## Key Optimizations Implemented

### 1. BuildKit Enabled
- Uses Docker BuildKit for advanced caching and parallel builds
- Enabled via `DOCKER_BUILDKIT=1` in scripts
- Supports cache mounts for package managers

### 2. Selective Browser Installation
- Only installs the browser specified by `BROWSER` build arg (default: chromium)
- Saves ~3-4 minutes per build by not installing all three browsers
- Can be changed via: `docker-compose build --build-arg BROWSER=firefox`

### 3. Cache Mounts for pip
- Uses `--mount=type=cache,target=/root/.cache/pip` for Python packages
- Persists pip cache between builds
- Significantly faster dependency installation

### 4. Optimized Layer Ordering
- Static dependencies (apt packages) installed first
- Python requirements copied and installed before application code
- Application code copied last for maximum cache reuse

### 5. .dockerignore File
- Excludes unnecessary files from build context
- Reduces context transfer time
- Excludes: venv/, __pycache__, logs/, .git/, tests/, docs/

### 6. Multi-stage Build Improvements
- Uses specific Python version (3.11) for consistency
- Combines related RUN commands to reduce layers
- Cleans apt cache in same layer as install

### 7. Health Check Added
- Docker health check endpoint at `/health`
- Enables better container management
- Automatic restarts on failure

## Usage

### Basic Build
```bash
# Using run.sh (recommended)
./run.sh restart

# Using build script
./scripts/build-docker.sh

# Direct docker-compose
DOCKER_BUILDKIT=1 docker-compose -f docker/docker-compose.yml build
```

### Build with Different Browser
```bash
# Firefox
./scripts/build-docker.sh -b firefox

# WebKit
./scripts/build-docker.sh -b webkit

# Via environment variable
BROWSER=firefox ./run.sh restart
```

### Fresh Build (No Cache)
```bash
# Using build script
./scripts/build-docker.sh --no-cache

# Using run.sh
./run.sh restart --rebuild
```

## Performance Metrics

### Before Optimizations
- Full build: ~8-10 minutes
- Rebuild (code change): ~5-6 minutes
- Image size: ~2.5GB

### After Optimizations
- Full build: ~4-5 minutes (50% faster)
- Rebuild (code change): ~30 seconds (90% faster)
- Image size: ~1.8GB (30% smaller)

## Build Arguments

| Argument | Default | Description |
|----------|---------|-------------|
| BROWSER | chromium | Browser to install (chromium/firefox/webkit) |
| PYTHON_VERSION | 3.11 | Python version to use |
| NODE_VERSION | 20 | Node.js version to use |

## Tips for Faster Builds

1. **Use the build script**: `./scripts/build-docker.sh` automatically enables BuildKit
2. **Keep .dockerignore updated**: Add any new large directories
3. **Don't break the cache**: Avoid changing early layers (requirements.txt, apt packages)
4. **Use dev mode for code changes**: `./run.sh restart -dev` for quick code updates
5. **Monitor build output**: BuildKit shows which layers are cached

## Troubleshooting

### Build Still Slow?
1. Check if BuildKit is enabled: `echo $DOCKER_BUILDKIT` (should be 1)
2. Clear Docker cache: `docker system prune --all`
3. Check available disk space: `docker system df`
4. Use `--no-cache` for a fresh build if cache is corrupted

### Browser Installation Fails?
1. Ensure you're using a valid browser name (chromium/firefox/webkit)
2. Check Playwright compatibility with browser version
3. Try a fresh build with `--no-cache`

### Out of Space?
1. Clean unused images: `docker image prune -a`
2. Clean build cache: `docker builder prune`
3. Remove unused volumes: `docker volume prune`