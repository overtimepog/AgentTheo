# Task Breakdown: Theo Agent MVP

## Overview
Total Tasks: 6 Task Groups, ~45 sub-tasks

This is a greenfield MVP for an agentic security research assistant with:
- LangGraph ReAct agent with streaming
- Textual TUI (three-panel layout)
- Docker container management (Kali Linux)
- Three tools: shell execution, file upload, file download
- OpenRouter LLM integration

## Task List

### Project Foundation

#### Task Group 1: Project Setup and Configuration
**Dependencies:** None

- [x] 1.0 Complete project foundation
  - [x] 1.1 Write 4-6 focused tests for configuration and project structure
    - Test Pydantic settings load from environment variables
    - Test missing OPENROUTER_API_KEY raises appropriate error
    - Test default model configuration
    - Test custom model override via OPENROUTER_MODEL env var
  - [x] 1.2 Create project directory structure
    - Create `theo-agent/` root directory
    - Create `src/theo/` package with `__init__.py`
    - Create subdirectories: `agent/`, `tools/`, `container/`, `tui/`
    - Create `tests/` directory with `conftest.py`
  - [x] 1.3 Create `pyproject.toml` with dependencies
    - Runtime: langchain-core>=0.3.0, langgraph>=0.6.0, textual>=0.80.0, rich>=13.0.0, docker>=7.0.0, httpx>=0.27.0, pydantic>=2.0.0, pydantic-settings>=2.0.0
    - Dev: pytest>=8.0.0, pytest-asyncio>=0.23.0, pytest-cov>=4.0.0, ruff>=0.4.0, mypy>=1.0.0
    - Configure ruff: target-version="py311", line-length=100
    - Define entry point: `theo = theo.tui.app:main`
  - [x] 1.4 Implement configuration module (`src/theo/config.py`)
    - Pydantic BaseSettings class for configuration
    - Fields: `openrouter_api_key` (required), `openrouter_model` (default: "arcee-ai/trinity-mini"), `openrouter_base_url` (default: "https://openrouter.ai/api/v1")
    - Environment variable prefixes: `OPENROUTER_`
    - Validation for required API key
  - [x] 1.5 Create base tool interface (`src/theo/tools/base.py`)
    - Abstract base class or protocol for tool interface
    - Common error handling patterns
    - Type definitions for tool inputs/outputs
  - [x] 1.6 Ensure project setup tests pass
    - Run ONLY the 4-6 tests written in 1.1
    - Verify `uv pip install -e .` succeeds
    - Verify imports work correctly

**Acceptance Criteria:**
- Project structure matches spec layout
- `uv pip install -e ".[dev]"` installs all dependencies
- Configuration loads from environment variables
- Ruff linting passes with zero errors
- Tests from 1.1 pass

---

### Container Layer

#### Task Group 2: Docker Container Management
**Dependencies:** Task Group 1

- [x] 2.0 Complete container management layer
  - [x] 2.1 Write 4-6 focused tests for container lifecycle
    - Test container creation with correct image (kalilinux/kali-rolling)
    - Test container configuration (detach=True, tty=True, stdin_open=True)
    - Test container removal on manager cleanup
    - Test exec_run returns streaming iterator
    - Test error handling when Docker daemon unavailable
  - [x] 2.2 Implement ContainerManager class (`src/theo/container/manager.py`)
    - Initialize docker client via `docker.from_env()`
    - `start()` method: create and start Kali container
    - `stop()` method: remove container with `force=True`
    - `exec_command(cmd)` method: execute command with `stream=True, demux=True`
    - Context manager protocol (`__aenter__`, `__aexit__`) for lifecycle
  - [x] 2.3 Implement streaming output handler
    - Parse demuxed stdout/stderr from exec_run
    - Yield chunks as they arrive for real-time display
    - Handle exit codes and error states
  - [x] 2.4 Add container health checks
    - Verify container is running before exec
    - Detect and handle container crashes
    - Provide meaningful error messages for common failures
  - [x] 2.5 Implement file transfer methods for container
    - `put_file(local_path, container_path)`: use `container.put_archive()`
    - `get_file(container_path, local_path)`: use `container.get_archive()`
    - Handle tar archive creation/extraction
  - [x] 2.6 Ensure container layer tests pass
    - Run ONLY the 4-6 tests written in 2.1
    - Verify container creates and destroys correctly
    - Do NOT run entire test suite

**Acceptance Criteria:**
- Container starts with kalilinux/kali-rolling image
- Commands execute with streaming output
- Container reliably removed on cleanup
- File transfer methods work correctly
- Tests from 2.1 pass

---

### Tools Layer

#### Task Group 3: Tool Implementations
**Dependencies:** Task Group 2

- [x] 3.0 Complete tool implementations
  - [x] 3.1 Write 6-8 focused tests for all three tools
    - Test shell tool executes command and returns output
    - Test shell tool handles command errors gracefully
    - Test shell tool streams output correctly
    - Test file upload creates file in container at specified path
    - Test file upload handles missing local file
    - Test file download retrieves file from container
    - Test file download handles missing container file
    - Test file download creates local directory if needed
  - [x] 3.2 Implement shell command tool (`src/theo/tools/shell.py`)
    - Use `@tool` decorator from langchain_core.tools
    - Input: command string
    - Call ContainerManager.exec_command()
    - Return structured result with stdout, stderr, exit_code
    - Include docstring for LLM tool description
  - [x] 3.3 Implement file upload tool (`src/theo/tools/files.py`)
    - Use `@tool` decorator
    - Input: local_path (str), container_path (str)
    - Validate local file exists before transfer
    - Call ContainerManager.put_file()
    - Return success/failure with paths
  - [x] 3.4 Implement file download tool (`src/theo/tools/files.py`)
    - Use `@tool` decorator
    - Input: container_path (str), local_path (str)
    - Call ContainerManager.get_file()
    - Create local directory if it doesn't exist
    - Return success/failure with paths and file size
  - [x] 3.5 Create tool registry (`src/theo/tools/__init__.py`)
    - Export all tools as a list for agent registration
    - Provide factory function that accepts ContainerManager instance
    - Ensure tools have access to container manager
  - [x] 3.6 Ensure tool layer tests pass
    - Run ONLY the 6-8 tests written in 3.1
    - Verify each tool functions correctly with mock container
    - Do NOT run entire test suite

**Acceptance Criteria:**
- Shell tool executes commands with streaming output
- File upload transfers files to container
- File download retrieves files from container
- All tools have proper LangChain tool definitions
- Tests from 3.1 pass

---

### Agent Layer

#### Task Group 4: LangGraph Agent Core
**Dependencies:** Task Group 3

- [x] 4.0 Complete LangGraph agent implementation
  - [x] 4.1 Write 4-6 focused tests for agent functionality
    - Test agent processes user message and returns response
    - Test agent invokes tools when appropriate
    - Test agent streams reasoning tokens
    - Test agent handles tool errors gracefully
    - Test conversation history is maintained within session
  - [x] 4.2 Define agent state model (`src/theo/agent/state.py`)
    - State class with messages list (conversation history)
    - Use TypedDict or Pydantic model
    - Include any additional state fields needed for reasoning
  - [x] 4.3 Create system prompts (`src/theo/agent/prompts.py`)
    - Security research assistant persona
    - Instructions for tool usage (shell, file upload, file download)
    - Guidelines for explaining reasoning and methodology
    - Clear boundaries on what the agent should/shouldn't do
  - [x] 4.4 Implement agent graph (`src/theo/agent/graph.py`)
    - Use `create_react_agent` from langgraph.prebuilt
    - Configure with OpenRouter-compatible LLM client
    - Register tools via ToolNode
    - Enable streaming with `stream_mode="messages"`
    - Implement in-memory conversation history
  - [x] 4.5 Configure OpenRouter LLM integration
    - Use langchain-openai ChatOpenAI with custom base_url
    - Load API key and model from config
    - Set appropriate headers for OpenRouter (HTTP-Referer, X-Title)
  - [x] 4.6 Create agent factory function
    - Accept ContainerManager instance
    - Build and return configured agent graph
    - Support async iteration for streaming responses
  - [x] 4.7 Ensure agent layer tests pass
    - Run ONLY the 4-6 tests written in 4.1
    - Verify agent responds and uses tools correctly
    - Do NOT run entire test suite

**Acceptance Criteria:**
- Agent responds to natural language queries
- Agent automatically calls tools when needed (no confirmation)
- Reasoning traces stream in real-time
- Conversation history maintained within session
- Tests from 4.1 pass

---

### TUI Layer

#### Task Group 5: Textual TUI Implementation
**Dependencies:** Task Group 4

- [x] 5.0 Complete Textual TUI implementation
  - [x] 5.1 Write 4-6 focused tests for TUI components
    - Test app initializes with three-panel layout
    - Test user input submission triggers agent invocation
    - Test conversation widget renders markdown
    - Test reasoning panel updates with streaming content
    - Test error messages display with distinct styling
  - [x] 5.2 Create main application class (`src/theo/tui/app.py`)
    - Extend textual.app.App
    - Initialize ContainerManager on startup
    - Initialize agent graph on startup
    - Cleanup container on app exit
    - Define CSS for three-panel layout
  - [x] 5.3 Implement conversation widget (`src/theo/tui/widgets/conversation.py`)
    - Extend or compose with RichLog
    - Render user messages and agent responses
    - Use Rich Markdown for response formatting
    - Auto-scroll to latest message
    - Distinct styling for error messages (red/warning)
  - [x] 5.4 Implement reasoning panel (`src/theo/tui/widgets/reasoning.py`)
    - Wrap RichLog in Collapsible widget
    - Stream reasoning tokens as they arrive
    - Auto-scroll to latest content
    - Clear on new conversation turn
  - [x] 5.5 Implement input widget (`src/theo/tui/widgets/input.py`)
    - Use textual.widgets.Input
    - Submit on Enter key
    - Input history navigation (Up/Down arrows)
    - Clear input after submission
  - [x] 5.6 Create main screen layout (`src/theo/tui/screens/main.py`)
    - CSS grid/flexbox for three-panel layout
    - Conversation area: center, flexible width
    - Reasoning panel: right side, collapsible
    - Input area: bottom, fixed height
    - Responsive sizing
  - [x] 5.7 Wire up agent-TUI integration
    - Connect input submission to agent invocation
    - Stream agent responses to conversation widget
    - Stream reasoning traces to reasoning panel
    - Handle tool execution output in conversation
  - [x] 5.8 Implement keyboard shortcuts
    - Ctrl+C: Interrupt/exit application
    - Standard Textual defaults for navigation
    - Input history with Up/Down in input widget
  - [x] 5.9 Add startup/shutdown handling
    - Show loading indicator while container starts
    - Display startup confirmation message
    - Graceful shutdown with container cleanup
    - Handle Docker daemon connection errors
  - [x] 5.10 Ensure TUI layer tests pass
    - Run ONLY the 4-6 tests written in 5.1
    - Verify layout renders correctly
    - Do NOT run entire test suite

**Acceptance Criteria:**
- Three-panel layout renders correctly
- User can type messages and see responses
- Reasoning streams to collapsible panel
- Markdown renders in conversation
- Errors display inline with distinct styling
- Tests from 5.1 pass

---

### Integration & Testing

#### Task Group 6: Integration Testing and Polish
**Dependencies:** Task Groups 1-5

- [x] 6.0 Complete integration testing and polish
  - [x] 6.1 Review tests from Task Groups 1-5
    - Review 4-6 tests from project setup (Task 1.1)
    - Review 4-6 tests from container layer (Task 2.1)
    - Review 6-8 tests from tools layer (Task 3.1)
    - Review 4-6 tests from agent layer (Task 4.1)
    - Review 4-6 tests from TUI layer (Task 5.1)
    - Total existing tests: approximately 22-32 tests
  - [x] 6.2 Identify critical integration gaps
    - End-to-end: user message -> agent -> tool -> container -> response
    - Container lifecycle: create on start, destroy on exit
    - File transfer roundtrip: upload then download
    - Error propagation: API errors, container errors, tool errors
  - [x] 6.3 Write up to 8 integration tests to fill gaps
    - Test full conversation flow with tool execution
    - Test container cleanup on normal exit
    - Test container cleanup on exception/crash
    - Test OpenRouter API error handling
    - Test file upload and download roundtrip
    - Test error messages appear in conversation
    - Test reasoning panel clears between turns
    - Test graceful handling of missing Docker daemon
  - [x] 6.4 Run complete feature test suite
    - Run all tests from Task Groups 1-5 plus integration tests
    - Expected total: approximately 30-40 tests
    - Fix any regressions discovered
    - Verify all success criteria met
  - [x] 6.5 Manual end-to-end testing
    - Launch TUI and verify container starts
    - Send natural language command and verify response
    - Request shell command execution (e.g., "run whoami")
    - Upload a test file to container
    - Download a file from container
    - Verify reasoning panel shows traces
    - Exit and verify container destroyed
  - [x] 6.6 Code quality pass
    - Run ruff linting and fix all issues
    - Run mypy type checking (if configured)
    - Review all docstrings and comments
    - Ensure consistent code style across modules

**Acceptance Criteria:**
- All feature-specific tests pass (30-40 tests total)
- End-to-end workflow functions correctly
- No ruff linting errors
- All success criteria from spec.md are met:
  - User can launch TUI and see fresh Kali container created
  - User can send natural language messages and receive streamed responses
  - Agent reasoning traces appear in real-time in collapsible panel
  - User can ask agent to run shell commands
  - Agent executes commands automatically without confirmation prompts
  - Command output streams back and displays in conversation
  - User can upload a file from local machine to container
  - User can download a file from container to local machine
  - Errors display inline with distinct styling
  - Container is destroyed when TUI exits
  - Application handles OpenRouter API errors gracefully

---

## Execution Order

Recommended implementation sequence:

1. **Task Group 1: Project Setup** - Foundation for all other work
2. **Task Group 2: Container Management** - Required by tools
3. **Task Group 3: Tools** - Required by agent
4. **Task Group 4: Agent Core** - Required by TUI
5. **Task Group 5: TUI** - User-facing interface
6. **Task Group 6: Integration** - Final validation

## Notes

- This is a greenfield project with no existing code to leverage
- No visual mockups provided; use Claude Code TUI as design reference
- MVP scope explicitly excludes: persistence, volume mounting, model switching UI, confirmation prompts, nmap tool, browser automation, Metasploit integration
- Container lifecycle is per-session only (no state persistence)
- All tool execution is automatic (no human-in-the-loop for MVP)
