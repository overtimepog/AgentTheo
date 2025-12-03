# Theo Agent MVP - Requirements

## User Answers to Clarifying Questions

### 1. TUI Layout and Panels
**Decision:** Three-panel layout similar to Claude Code:
- Main conversation area in the center
- Input area at the bottom
- Collapsible reasoning panel on the right side

### 2. Reasoning Display Behavior
**Decision:**
- Clear reasoning traces when a new conversation starts
- Auto-scroll to latest content as traces stream in
- Reasoning persists within a single conversation turn

### 3. Tool Execution Confirmation
**Decision:** Execute commands/tools automatically without user confirmation
- No human-in-the-loop required for shell commands in MVP
- Agent has autonomy to run tools as needed

### 4. Container Lifecycle
**Decision:** Each session spawns a fresh container
- Container is destroyed when TUI exits
- No state persistence between sessions
- **NEW REQUIREMENT:** Add tools that allow the agent to transfer files to/from the local machine
  - This enables saving important findings before container destruction
  - Tools needed: file upload to container, file download from container

### 5. Error Handling UX
**Decision:** Option A - Inline in the conversation as styled error messages
- Errors appear naturally in the conversation flow
- Styled distinctly (e.g., red/warning colors) to stand out
- No separate notification area or modals

### 6. Model Switching
**Decision:** Configuration via environment variable only for MVP
- No `/model` command needed
- Set model via `OPENROUTER_MODEL` environment variable
- Simplifies MVP scope

### 7. Keyboard Navigation
**Decision:** Standard terminal keybindings:
- Ctrl+C to interrupt
- Up/Down for input history
- Standard Textual defaults for panel navigation

### 8. Scope Boundaries

**INCLUDED in MVP:**
- Markdown rendering in responses (Rich markdown support)

**EXCLUDED from MVP:**
- Conversation persistence to disk
- Syntax highlighting for code blocks (beyond markdown)
- Container volume mounting for persistent data

---

## Updated Feature List

Based on user feedback, the MVP now includes:

1. **LangGraph Agent Core** - ReAct agent with StateGraph, streaming, tool calling
2. **Basic Terminal UI** - Textual TUI with:
   - Main conversation area (center)
   - Input area (bottom)
   - Collapsible reasoning panel (right)
   - Markdown rendering for responses
   - Inline error display
   - Auto-scroll in reasoning panel
3. **Fresh Kali Container per Session** - Container lifecycle:
   - Create new container on TUI launch
   - Destroy container on TUI exit
   - No persistence between sessions
4. **Shell Command Tool** - Execute commands with streaming output
5. **File Transfer Tools** - NEW: Upload/download files between local machine and container
6. **OpenRouter LLM Integration** - Environment variable configuration

---

## Visual Assets
No visual assets provided - proceeding with Claude Code-style design reference.
