# Specification: Theo Agent MVP

## Goal

Build the foundational MVP of Theo Agent: an agentic security research assistant with a Claude Code-style terminal interface that executes shell commands in an isolated Kali Linux container while streaming reasoning traces in real-time.

## User Stories

- As a penetration tester, I want to issue natural language commands that execute security tools so that I can focus on methodology rather than tool syntax
- As a security student, I want to see the agent's reasoning process so that I can learn penetration testing methodology through demonstration
- As a red team operator, I want to transfer files to/from the container so that I can save important findings before the session ends
- As a security researcher, I want automatic tool execution without confirmations so that I can work quickly without interruption

## Core Requirements

- User can type natural language messages and receive AI-generated responses with markdown rendering
- Agent automatically executes shell commands inside a Kali container without confirmation prompts
- Reasoning traces stream in real-time to a collapsible side panel
- Fresh Kali container spawns on TUI launch and destroys on exit
- User can upload files from local machine to container
- User can download files from container to local machine
- Errors display inline in conversation with distinct styling

## Visual Design

No mockups provided. Reference Claude Code TUI for design patterns:

- Three-panel layout: main conversation (center), input (bottom), reasoning (right collapsible)
- Auto-scroll in reasoning panel as traces stream
- Clear reasoning traces on new conversation
- Markdown rendering for agent responses
- Distinct error styling (e.g., red/warning colors)

## Reusable Components

### Existing Code to Leverage

This is a greenfield project. No existing Theo Agent implementation exists in the codebase.

### External Libraries (per tech-stack.md)

- LangGraph 0.6+ with `create_react_agent` for ReAct pattern
- Textual 0.80+ with `RichLog`, `Input`, `Collapsible` widgets
- docker-py 7.0+ for container lifecycle
- Rich for markdown rendering

### New Components Required

All components are new:

1. **Agent Core** (`src/theo/agent/`)
   - `graph.py`: LangGraph StateGraph with ReAct agent
   - `state.py`: Agent state model
   - `prompts.py`: System prompts for security assistant persona

2. **Container Manager** (`src/theo/container/`)
   - `manager.py`: Docker lifecycle (create, exec, stream, destroy)

3. **Tools** (`src/theo/tools/`)
   - `shell.py`: Shell command execution with streaming
   - `file_upload.py`: Local-to-container file transfer
   - `file_download.py`: Container-to-local file transfer

4. **TUI** (`src/theo/tui/`)
   - `app.py`: Main Textual application
   - `widgets/conversation.py`: Scrollable conversation with markdown
   - `widgets/reasoning.py`: Collapsible streaming reasoning panel
   - `widgets/input.py`: Message input area

5. **Configuration** (`src/theo/config.py`)
   - Pydantic settings for OpenRouter API, model selection

## Technical Approach

### LangGraph Agent (ReAct Pattern)

Use `create_react_agent` from LangGraph with streaming enabled. The agent receives user messages, reasons about tool usage, executes tools, and returns responses. Key configuration:

- Streaming: Enable `stream_mode="messages"` for real-time reasoning visibility
- Tools: Register shell, file upload, and file download tools via `ToolNode`
- Memory: In-memory conversation history (no persistence to disk per requirements)

### Container Lifecycle

Per-session container model:

1. On TUI startup: `client.containers.run("kalilinux/kali-rolling", detach=True, tty=True, stdin_open=True)`
2. During session: `container.exec_run(cmd, stream=True, demux=True)` for shell commands
3. On TUI exit: `container.remove(force=True)`

No volume mounting. No state persistence between sessions.

### Tool Definitions (6 tools total, 3 for MVP)

1. **Shell Command Tool**
   - Input: command string
   - Execution: `exec_run` with streaming
   - Output: stdout/stderr as structured result

2. **File Upload Tool**
   - Input: local file path, container destination path
   - Execution: Use `container.put_archive()` to transfer files
   - Output: success/failure with paths

3. **File Download Tool**
   - Input: container file path, local destination path
   - Execution: Use `container.get_archive()` to retrieve files
   - Output: success/failure with paths

### OpenRouter Integration

- API base: `https://openrouter.ai/api/v1`
- Model: `arcee-ai/trinity-mini` (configurable via `OPENROUTER_MODEL` env var)
- Authentication: `OPENROUTER_API_KEY` environment variable
- Use LangChain's OpenAI-compatible client with custom base URL

### TUI Architecture

Textual app with three main regions:

```
+---------------------------+-------------+
|                           |  Reasoning  |
|    Conversation Area      |   Panel     |
|    (RichLog + Markdown)   | (Collapsible|
|                           |  RichLog)   |
+---------------------------+-------------+
|        Input Area (Input widget)        |
+-----------------------------------------+
```

- Main screen composed via CSS grid/flexbox
- Conversation widget: `RichLog` with Rich markdown rendering
- Reasoning panel: `Collapsible` containing `RichLog`, auto-scroll enabled
- Input: Standard `Input` widget with submit on Enter

### Keyboard Shortcuts

- Ctrl+C: Interrupt/exit
- Up/Down in input: Navigate input history
- Standard Textual defaults for panel navigation

## Out of Scope

- Conversation persistence to disk (no save/restore sessions)
- Syntax highlighting beyond Rich markdown defaults
- Container volume mounting
- Model switching UI (configuration only via env var)
- Human-in-the-loop confirmation for tool execution
- Nmap tool (roadmap item 6)
- Browser automation tool (roadmap item 7)
- Metasploit integration (roadmap item 10)
- Multi-agent orchestration (roadmap item 11)
- Finding tracker system (roadmap item 9)
- Extensible tool framework (roadmap item 12)

## Success Criteria

- User can launch TUI and see a fresh Kali container created
- User can send natural language messages and receive streamed responses
- Agent reasoning traces appear in real-time in collapsible panel
- User can ask agent to run shell commands (e.g., "run nmap -sV localhost")
- Agent executes commands automatically without confirmation prompts
- Command output streams back and displays in conversation
- User can upload a file from local machine to container
- User can download a file from container to local machine
- Errors display inline with distinct styling
- Container is destroyed when TUI exits
- Application handles OpenRouter API errors gracefully
