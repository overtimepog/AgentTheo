# Browser Agent - Desktop Mode

A containerized browser automation agent using Playwright, LangGraph, and OpenRouter API that executes tasks through natural language commands with a visible GUI.

> **Note**: This browser agent runs exclusively in desktop mode with VNC/noVNC access for visual debugging and monitoring.

## Features

- 🤖 Natural language task execution
- 🌐 Multi-browser support (Chromium, Firefox, WebKit)
- 📊 Real-time visual feedback via VNC/noVNC
- 🔧 Docker containerized environment
- 🧠 LLM-powered decision making via OpenRouter
- 🎯 Playwright browser automation
- 🖥️ Always-on desktop mode with GUI visibility

## Quick Start

```bash
# Clone the repository
git clone https://github.com/yourusername/browser-agent.git
cd browser-agent

# Set up environment variables
cp config/.env.template config/.env
# Edit config/.env with your OpenRouter API key

# Run a task
./run.sh task "go to google and search for AI news"

# Access the browser GUI
# Open http://localhost:6080/vnc.html in your browser
```

## Prerequisites

- Docker installed and running
- OpenRouter API key (get one at https://openrouter.ai)

## Usage

The agent accepts natural language commands to perform browser automation tasks:

```bash
./run.sh task "navigate to amazon and find the price of headphones"
./run.sh task "fill out the contact form on example.com"
./run.sh task "extract all product listings from the search results"
```

### Accessing the Browser GUI

When you run a task, the browser runs with a full desktop environment:

- **Web Interface**: Open http://localhost:6080/vnc.html in your browser
- **VNC Client**: Connect to vnc://localhost:5901 (no password)

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

### Rebuilding the Container

```bash
./run.sh restart
```

This rebuilds the Docker image with any code changes.

### Environment Variables

Key environment variables in `config/.env`:
- `OPENROUTER_API_KEY`: Your OpenRouter API key
- `BROWSER`: Browser choice (chromium/firefox/webkit)
- `LOG_LEVEL`: Logging verbosity (INFO/DEBUG/WARNING)

### Project Structure

```
browser-agent/
├── agent/           # Core agent implementation
├── config/          # Configuration files
├── docker/          # Docker configuration
├── docs/           # Documentation
├── logs/           # Application logs
└── run.sh          # Main entry point
```

## Troubleshooting

### Can't connect to VNC/noVNC
- Ensure Docker is running
- Check ports 5901 and 6080 are not in use
- Try restarting the container: `docker stop browser-agent && ./run.sh task "..."`

### Browser crashes
- Increase Docker memory allocation
- Check logs: `docker logs browser-agent`

### Task fails
- Check your OpenRouter API key is set correctly
- Ensure the website is accessible
- Review logs for specific errors

## License

MIT License - see LICENSE file for details