# Browser Agent Architecture

## Overview

The Browser Agent is a containerized automation system that combines LangChain's orchestration capabilities with Playwright's browser automation tools, powered by OpenRouter's free LLM models.

## Components

### 1. Docker Container Environment
- **Base Image**: Node.js 20 with Debian Bookworm
- **Browsers**: Pre-installed Chromium, Firefox, and WebKit
- **Runtime**: Python 3 with virtual environment
- **Security**: Non-root user execution

### 2. Agent Core (Python)

#### main.py
- Main `BrowserAgent` class
- Handles initialization, task execution, and cleanup
- Integrates all components

#### browser_tools.py
- Playwright browser instance management
- LangChain browser toolkit integration
- Provides browser automation tools

#### llm_client.py
- OpenRouter API integration
- Custom LLM implementation for LangChain
- Supports free DeepSeek models

#### logger.py- Real-time logging with color support
- File and console output
- Docker-friendly streaming

#### task_executor.py
- Task parsing and classification
- Retry logic with exponential backoff
- Execution strategy management

### 3. CLI Interface
- **run.sh**: Main entry point
- Parameter validation
- Docker lifecycle management
- Real-time log streaming

## Data Flow

1. User executes: `./run.sh task "natural language command"`
2. run.sh validates input and starts Docker container
3. Container runs entrypoint.py with task description
4. BrowserAgent initializes:
   - Creates Playwright browser instance
   - Initializes OpenRouter LLM client
   - Sets up LangChain agent with browser tools
5. Agent processes natural language task
6. Browser tools execute actions
7. Results stream to console in real-time
8. Cleanup and container shutdown

## Available Browser Tools

- **navigate_browser**: Navigate to URLs
- **click_element**: Click on page elements
- **extract_text**: Extract page content
- **extract_hyperlinks**: Get all links
- **get_elements**: Query DOM elements
- **current_page**: Get current URL
- **previous_page**: Navigate back

## Configuration

Environment variables control behavior:
- `OPENROUTER_API_KEY`: API authentication
- `BROWSER`: Browser choice (chromium/firefox/webkit)
- `HEADLESS`: Run browsers headlessly
- `LOG_LEVEL`: Logging verbosity
- `LLM_MODEL`: OpenRouter model selection

## Security Considerations

- Runs as non-root user in container
- Browser sandboxing enabled
- No persistent storage of credentials
- Isolated execution environment