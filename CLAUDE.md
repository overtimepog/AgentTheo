# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

AgentTheo is a containerized browser automation agent that combines LLMs with Playwright for intelligent web automation. The project uses a Web UI-first architecture with real-time streaming and visual feedback through VNC.

## Architecture

### Core Components

1. **Main Orchestrator** (`agent/core/main.py`): Analyzes user requests and delegates to specialized agents
2. **Browser Agent** (`agent/browser/agent.py`): Handles all web automation tasks using Playwright
3. **Web UI Server** (`webui/server.py`): FastAPI application with WebSocket and SSE support for real-time streaming
4. **Stealth System** (`agent/browser/stealth/`): Advanced anti-detection features to avoid CAPTCHAs

### Key Technologies

- **Python 3.13** with async/await patterns
- **LangGraph/LangChain** for agent orchestration
- **Playwright** for browser automation
- **FastAPI** with WebSockets and SSE for streaming
- **Docker** with multi-stage builds
- **noVNC** for browser visual feedback

## Development Commands

All operations use the `run.sh` script:

```bash
# Standard run (auto-detects changes)
./run.sh

# Development mode (quick rebuilds, skips some steps)
./run.sh -dev

# Hot reload mode (mounts code as volumes, auto-reloads)
./run.sh -hot

# Force complete rebuild
./run.sh --rebuild

# Run tests
./run.sh test

# Clean everything
./run.sh clean
```

## Testing

```bash
# Run all tests
./run.sh test

# Test stealth features specifically
python -m pytest tests/test_stealth.py -v

# Test browser agent
python -m pytest tests/test_browser_agent.py -v
```

## Code Organization Patterns

### Agent Pattern
- Main orchestrator receives tasks and determines which agent to use
- Specialized agents (browser, future agents) handle specific task types
- All agents use LangGraph for state management

### Browser Automation
- All browser interactions go through `agent/browser/tools/`
- Stealth features are applied automatically via `agent/browser/stealth/`
- Browser context is managed by `BrowserManager` class

### Streaming Architecture
- Web UI uses SSE for agent responses
- WebSockets for browser state updates
- Frontend handles reconnection automatically

## Key Development Guidelines

### When Working with Browser Code
- Always consider stealth implications when modifying browser behavior
- Test changes against popular anti-bot services
- Use existing browser tools rather than raw Playwright calls

### When Adding New Features
- New agent capabilities should be added as separate agents under `agent/`
- Browser tools go in `agent/browser/tools/`
- Web UI updates require changes to both `webui/server.py` and `webui/static/`

### When Modifying the Web UI
- Streaming responses use SSE endpoint `/api/chat/stream`
- WebSocket at `/ws` for browser state updates
- Frontend JavaScript uses vanilla JS with no framework

## Environment Configuration

Required environment variables in `config/.env`:
- `OPENROUTER_API_KEY`: For LLM access
- `BROWSER`: Browser choice (chromium/firefox/webkit)
- `LOG_LEVEL`: Logging verbosity (DEBUG/INFO/WARNING/ERROR)

## Common Tasks

### Adding a New Browser Tool
1. Create tool in `agent/browser/tools/`
2. Register in `agent/browser/agent.py`
3. Add tests in `tests/test_browser_agent.py`

### Implementing a New Agent
1. Create agent module under `agent/`
2. Define agent using LangGraph StateGraph
3. Register in main orchestrator
4. Add routing logic in `agent/core/main.py`

### Enhancing Stealth Features
1. Add feature to `agent/browser/stealth/`
2. Apply in `stealth_browser.py`
3. Test against detection services
4. Document in stealth README

## Important Architectural Decisions

1. **Web UI First**: All features should be accessible through the web interface
2. **Streaming by Default**: Use SSE/WebSockets for real-time feedback
3. **Containerized Environment**: Everything runs in Docker for consistency
4. **Stealth is Critical**: Browser automation must avoid detection
5. **Orchestrator Pattern**: Main agent delegates rather than doing everything

## Integration Points

- **OpenRouter API**: All LLM calls go through `agent/llm/client.py`
- **Playwright**: Browser automation via `agent/browser/browser_manager.py`
- **Docker**: Multi-stage build in `docker/Dockerfile`
- **VNC**: Visual feedback through `docker/docker-compose.yml` noVNC service