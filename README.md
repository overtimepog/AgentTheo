# AgentTheo

A containerized browser automation agent using Playwright, LangGraph, and OpenRouter API that executes tasks through natural language commands with a visible GUI and advanced anti-detection features.

> **Note**: AgentTheo runs exclusively in desktop mode with VNC/noVNC access for visual debugging and monitoring.

## Features

- 🤖 Natural language task execution
- 🌐 Multi-browser support (Chromium, Firefox, WebKit)
- 📊 Real-time visual feedback via VNC/noVNC
- 💬 **NEW: Web UI with integrated VNC viewer and chat interface**
- 🔧 Docker containerized environment
- 🧠 LLM-powered decision making via OpenRouter
- 🎯 Playwright browser automation
- 🖥️ Always-on desktop mode with GUI visibility
- 🥷 Advanced stealth features to avoid CAPTCHA and bot detection

## Prerequisites

- **Docker Desktop** installed and running ([Download Docker](https://www.docker.com/products/docker-desktop/))
- **OpenRouter API key** (get one at https://openrouter.ai)

## Quick Start

### 1. Initial Setup

```bash
# Clone the repository
git clone https://github.com/yourusername/AgentTheo.git
cd AgentTheo

# Set up environment variables
cp config/.env.template config/.env
# Edit config/.env and add your OpenRouter API key
```

### 2. Start AgentTheo

```bash
# Start AgentTheo with Web UI
./run.sh start
```

This will:
- Build the Docker image (first time only)
- Start all services (VNC, Web UI, Agent)
- Make the Web UI available at http://localhost:8000

### 3. Access the Web UI

Open your browser and navigate to:
- **http://localhost:8000**

The Web UI provides:
- Live VNC view of the browser on the left
- Chat interface on the right to send commands
- Real-time responses from the agent

## Usage

### Managing AgentTheo

```bash
# Start AgentTheo
./run.sh start

# Stop AgentTheo
./run.sh stop

# Restart AgentTheo
./run.sh restart

# Restart with rebuild
./run.sh restart --rebuild

# View logs
./run.sh logs

# Check status
./run.sh status
```

### Using the Web UI

1. Start AgentTheo: `./run.sh start`
2. Open http://localhost:8000 in your browser
3. Type commands in the chat interface
4. Watch the browser execute your commands in real-time

Example commands you can send through the chat:
- "Go to google and search for OpenAI news"
- "Navigate to amazon and find the price of headphones"
- "Fill out the contact form on example.com"
- "Find the latest news about artificial intelligence from multiple sources"
- "Extract all product listings from the search results"

### Monitoring Your Task

When you run a task, the browser runs with a full desktop environment:

1. **Use the Web UI (Recommended)**: Open http://localhost:8000
   - Integrated VNC viewer and chat interface
   - Send commands directly to the agent
   - See real-time responses
2. **Direct VNC Access**: Open http://localhost:6080/vnc.html
3. **Connect via VNC**: Use any VNC client to connect to `localhost:5901`
4. **View Logs**: `docker logs -f browser-agent`
5. **Stop Task**: `docker stop browser-agent`

This allows you to:
- Watch the automation in real-time
- Debug selector issues visually  
- Intervene if needed
- Record demos of your automation

### Web UI Features

The new web interface (http://localhost:8000) provides:
- **Split View**: VNC display on the left, chat interface on the right
- **Real-time Chat**: Send commands and receive responses from the agent
- **WebSocket Communication**: Instant bidirectional communication
- **Status Indicators**: Connection status and agent availability
- **Responsive Design**: Works on different screen sizes

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
AgentTheo/
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