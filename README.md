# Browser Agent - Desktop Mode with Advanced Stealth

A containerized browser automation agent using Playwright, LangGraph, and OpenRouter API that executes tasks through natural language commands with a visible GUI and advanced anti-detection features.

> **Note**: This browser agent runs exclusively in desktop mode with VNC/noVNC access for visual debugging and monitoring.

## Features

- 🤖 Natural language task execution
- 🌐 Multi-browser support (Chromium, Firefox, WebKit)
- 📊 Real-time visual feedback via VNC/noVNC
- 🔧 Docker containerized environment
- 🧠 LLM-powered decision making via OpenRouter
- 🎯 Playwright browser automation
- 🖥️ Always-on desktop mode with GUI visibility
- 🥷 **NEW: Advanced stealth features to avoid CAPTCHA and bot detection**

## Prerequisites

- **Docker Desktop** installed and running ([Download Docker](https://www.docker.com/products/docker-desktop/))
- **OpenRouter API key** (get one at https://openrouter.ai)

## Quick Start

### 1. Initial Setup

```bash
# Clone the repository
git clone https://github.com/yourusername/browser-agent.git
cd browser-agent

# Set up environment variables
cp config/.env.template config/.env
# Edit config/.env and add your OpenRouter API key
```

### 2. First Time Setup

Before running your first task, build the Docker container:

```bash
# Build the container (required on first run)
./run.sh restart
```

This command:
- Builds the Docker image with all dependencies
- Installs Playwright browsers
- Sets up the desktop environment
- Prepares the automation framework

### 3. Run Your First Task

```bash
# Run a browser automation task
./run.sh task "go to google and search for AI news"
```

### 4. Access the Browser GUI

Once the task is running, you can watch it in real-time:

- **Web Interface**: Open http://localhost:6080/vnc.html in your browser
- **VNC Client**: Connect to vnc://localhost:5901 (no password)

## Usage

### Running Tasks

The agent accepts natural language commands through the `run.sh` script:

```bash
# Basic syntax
./run.sh task "<your natural language command>"

# Examples
./run.sh task "navigate to amazon and find the price of headphones"
./run.sh task "fill out the contact form on example.com"
./run.sh task "extract all product listings from the search results"
./run.sh task "find the latest news about artificial intelligence"
```

### Command Reference

```bash
# Run a browser automation task
./run.sh task "<command>"

# Rebuild the container (after code changes or updates)
./run.sh restart

# View help
./run.sh
```

### Monitoring Your Task

When you run a task, the browser runs with a full desktop environment:

1. **Watch in Browser**: Open http://localhost:6080/vnc.html
2. **Connect via VNC**: Use any VNC client to connect to `localhost:5901`
3. **View Logs**: `docker logs -f browser-agent`
4. **Stop Task**: `docker stop browser-agent`

This allows you to:
- Watch the automation in real-time
- Debug selector issues visually  
- Intervene if needed
- Record demos of your automation

## Architecture

- **Docker Container**: Isolated environment with desktop components
- **Virtual Display**: Xvfb provides the display for the browser
- **VNC Server**: x11vnc shares the desktop
- **Web Access**: noVNC provides browser-based access
- **LangGraph Agent**: Graph-based agent orchestration
- **Playwright Toolkit**: Handles browser automation

## Development

### Container Management

```bash
# Rebuild after code changes
./run.sh restart

# Stop running container
docker stop browser-agent

# Remove container
docker rm browser-agent

# View container logs
docker logs -f browser-agent
```

### Environment Variables

Key environment variables in `config/.env`:
- `OPENROUTER_API_KEY`: Your OpenRouter API key
- `BROWSER`: Browser choice (chromium/firefox/webkit)
- `LOG_LEVEL`: Logging verbosity (INFO/DEBUG/WARNING)

### Project Structure

```
browser-agent/
├── agent/           # Core agent implementation
│   ├── core/        # Main agent logic
│   ├── stealth/     # Anti-detection features
│   ├── tools/       # Browser automation tools
│   └── utils/       # Utilities and logging
├── config/          # Configuration files
├── docker/          # Docker configuration
├── docs/            # Documentation
├── examples/        # Example scripts
├── logs/            # Application logs
├── tests/           # Test suite
└── run.sh          # Main entry point
```

## Stealth Features

The browser agent includes advanced stealth capabilities to avoid detection:

- **WebDriver Detection**: Removes `navigator.webdriver` property
- **Chrome Runtime**: Emulates genuine Chrome browser objects
- **WebGL Spoofing**: Randomizes graphics hardware information
- **Plugin Emulation**: Simulates common browser plugins
- **Fingerprint Randomization**: Varies browser fingerprints
- **Human-like Behavior**: Adds natural delays and interactions

For more details, see [docs/STEALTH_IMPLEMENTATION.md](docs/STEALTH_IMPLEMENTATION.md)

### Testing Stealth

Run the stealth test suite:
```bash
python tests/test_stealth.py
```

Try the stealth demo:
```bash
python examples/stealth_demo.py
```

## Troubleshooting

### Docker Issues
- **"Docker daemon is not running"**: Start Docker Desktop
- **"Cannot connect to Docker daemon"**: Ensure Docker Desktop is running
- **First run fails**: Always run `./run.sh restart` before your first task

### Can't Connect to Browser GUI
- Ensure Docker is running
- Check ports 5901 and 6080 are not in use
- Try restarting: `docker stop browser-agent && ./run.sh restart`
- Verify container is running: `docker ps`

### Browser Crashes
- Increase Docker memory allocation in Docker Desktop settings
- Check logs: `docker logs browser-agent`
- Rebuild container: `./run.sh restart`

### Task Fails
- Verify OpenRouter API key is set in `config/.env`
- Check if the LLM model supports function calling
- Ensure the target website is accessible
- Review logs for specific errors: `docker logs browser-agent`

### Common Fixes
```bash
# Full reset and rebuild
docker stop browser-agent
docker rm browser-agent
./run.sh restart

# Check what's running
docker ps -a

# Clean up old images
docker image prune
```

## License

MIT License - see LICENSE file for details