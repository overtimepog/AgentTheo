# Tech Stack

## Overview

Theo Agent is built on Python with LangGraph for agent orchestration, Textual for terminal UI, and Docker for isolated tool execution. This stack prioritizes async-first design for responsive streaming, strong typing for reliability, and modular architecture for extensibility.

---

## Core Framework

### Python 3.11+
**Purpose:** Primary programming language

**Rationale:** Python 3.11+ provides significant performance improvements (10-60% faster), enhanced error messages for debugging, and native support for modern async patterns. The security tooling ecosystem is Python-centric (nmap, Metasploit bindings, Playwright).

### LangGraph 0.6+
**Purpose:** Agent orchestration and workflow management

**Rationale:** LangGraph provides the StateGraph API for building complex agent workflows with:
- Native streaming support for real-time reasoning visibility
- Built-in `create_react_agent` for ReAct pattern implementation
- `ToolNode` for clean tool integration
- Checkpointing for conversation persistence
- Human-in-the-loop patterns for exploitation confirmation

**Key APIs:**
- `StateGraph` for agent state machine
- `create_react_agent` for ReAct agent creation
- `ToolNode` for tool execution nodes
- `MemorySaver` for conversation persistence

### LangChain Core
**Purpose:** Tool definitions and LLM abstractions

**Rationale:** Provides standardized interfaces for:
- `@tool` decorator for tool definition
- `BaseChatModel` abstraction for LLM switching
- Message types (`HumanMessage`, `AIMessage`, `ToolMessage`)
- Output parsers for structured responses

---

## LLM Integration

### OpenRouter
**Purpose:** LLM provider with model flexibility

**Rationale:** OpenRouter provides:
- OpenAI-compatible API reducing integration complexity
- Access to multiple models including arcee-ai/trinity-mini
- Single API key for multiple model providers
- Cost tracking and rate limiting

**Configuration:**
```python
# Environment variable: OPENROUTER_API_KEY
# Base URL: https://openrouter.ai/api/v1
# Default model: arcee-ai/trinity-mini
```

---

## Terminal UI

### Textual 0.80+
**Purpose:** Async-first terminal user interface framework

**Rationale:** Textual is built on Rich and provides:
- Native async/await support matching the agent's streaming architecture
- Reactive data binding for real-time updates
- Built-in widgets (Input, TextArea, DataTable, Collapsible)
- CSS-like styling for consistent visual design
- Composable component architecture

**Key Components:**
- `App` base class for application shell
- `Screen` for view management
- `Container` layouts for panel organization
- `RichLog` for streaming message display

### Rich
**Purpose:** Terminal formatting, markdown rendering, syntax highlighting

**Rationale:** Rich provides the rendering primitives Textual builds on:
- Markdown rendering for agent responses
- Syntax highlighting for code and tool output
- Tables and panels for structured data display
- Progress bars for long-running operations

---

## Container & Execution

### docker-py 7.0+
**Purpose:** Docker SDK for Python

**Rationale:** Programmatic container management with:
- Container lifecycle control (create, start, stop, remove)
- `exec_run` with `stream=True` for real-time command output
- Volume mounting for persistent data
- Network configuration for isolated testing environments

**Usage Pattern:**
```python
container = client.containers.run(
    "kalilinux/kali-rolling",
    detach=True,
    tty=True,
    stdin_open=True
)
exit_code, output = container.exec_run(
    cmd, stream=True, demux=True
)
```

### kalilinux/kali-rolling
**Purpose:** Official Kali Linux Docker image

**Rationale:** Pre-packaged security distribution with:
- 600+ security tools available via apt
- Regular updates tracking Debian testing
- Familiar environment for security professionals
- Smaller footprint than full Kali ISO

**Pre-installed Tools:**
- nmap, nikto, gobuster (reconnaissance)
- sqlmap, burpsuite-community (web testing)
- metasploit-framework (exploitation)
- john, hashcat (password cracking)

---

## Security Tools

### python-nmap
**Purpose:** Nmap wrapper for structured scan results

**Rationale:** Provides:
- Pythonic interface to nmap functionality
- Parsed XML output into dictionaries
- Async-compatible scan execution
- Structured access to hosts, ports, services

### pymetasploit3
**Purpose:** Metasploit RPC automation

**Rationale:** Enables programmatic Metasploit control:
- Module search and configuration
- Exploit execution and session management
- Loot and credential retrieval
- Console interaction

**Considerations:** Requires msfrpcd running in the Kali container

### Playwright
**Purpose:** Async browser automation

**Rationale:** Modern browser automation with:
- Native async/await API
- Chromium, Firefox, WebKit support
- Auto-wait functionality reducing flakiness
- Network interception for request modification
- Screenshot and PDF generation

---

## Infrastructure

### asyncio
**Purpose:** Async I/O for non-blocking operations

**Rationale:** Foundation for responsive streaming:
- Agent reasoning streams without blocking UI
- Multiple tool executions can run concurrently
- WebSocket and HTTP connections share event loop
- Native Python integration (no external runtime)

### httpx
**Purpose:** Async HTTP client

**Rationale:** Modern HTTP client with:
- Async/await support matching overall architecture
- HTTP/2 support for efficient API calls
- Streaming response handling
- Connection pooling

### pydantic 2.0+
**Purpose:** Data validation and settings management

**Rationale:** Type-safe configuration with:
- `BaseSettings` for environment variable parsing
- Automatic validation of tool inputs/outputs
- JSON schema generation for tool definitions
- Serialization for state persistence

---

## Development

### uv
**Purpose:** Fast Python package manager

**Rationale:** Modern package management with:
- 10-100x faster than pip
- Built-in virtual environment management
- Lock file support for reproducibility
- Drop-in pip compatibility

**Commands:**
```bash
uv venv
uv pip install -e ".[dev]"
uv pip compile requirements.in -o requirements.txt
```

### pytest
**Purpose:** Testing framework

**Rationale:** Standard Python testing with:
- Async test support via pytest-asyncio
- Fixture system for container setup/teardown
- Parameterized tests for tool variations
- Coverage reporting integration

### ruff
**Purpose:** Linting and formatting

**Rationale:** Single tool replacing multiple linters:
- 10-100x faster than flake8/black/isort
- Auto-fix capability
- Import sorting
- Compatible with existing configurations

**Configuration:**
```toml
[tool.ruff]
target-version = "py311"
line-length = 100
select = ["E", "F", "I", "N", "W", "UP"]
```

---

## Project Structure

```
theo-agent/
├── src/
│   └── theo/
│       ├── __init__.py
│       ├── agent/              # LangGraph agent implementation
│       │   ├── __init__.py
│       │   ├── graph.py        # StateGraph definition
│       │   ├── state.py        # Agent state model
│       │   └── prompts.py      # System prompts
│       ├── tools/              # Tool implementations
│       │   ├── __init__.py
│       │   ├── base.py         # Tool base class
│       │   ├── shell.py        # Shell command tool
│       │   ├── nmap.py         # Nmap tool
│       │   ├── browser.py      # Playwright tool
│       │   └── metasploit.py   # Metasploit tool
│       ├── container/          # Docker management
│       │   ├── __init__.py
│       │   └── manager.py      # Container lifecycle
│       ├── tui/                # Textual UI
│       │   ├── __init__.py
│       │   ├── app.py          # Main application
│       │   ├── screens/        # Screen definitions
│       │   └── widgets/        # Custom widgets
│       └── config.py           # Pydantic settings
├── tests/
├── pyproject.toml
└── README.md
```

---

## Dependencies Summary

### Runtime Dependencies
```
langchain-core>=0.3.0
langgraph>=0.6.0
textual>=0.80.0
rich>=13.0.0
docker>=7.0.0
python-nmap>=0.7.1
pymetasploit3>=1.0.0
playwright>=1.40.0
httpx>=0.27.0
pydantic>=2.0.0
pydantic-settings>=2.0.0
```

### Development Dependencies
```
pytest>=8.0.0
pytest-asyncio>=0.23.0
pytest-cov>=4.0.0
ruff>=0.4.0
mypy>=1.0.0
```
