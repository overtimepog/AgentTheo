# Theo

A modern, extensible AI agent framework with semantic memory, tool-calling, and subagent delegation.

Built with LangChain/LangGraph, OpenRouter, Qdrant vector database, and Rich terminal UI.

## Features

- **Conversational Agent** - Interactive chat with streaming responses
- **Semantic Memory** - Persistent vector-based memory with auto-retrieval
- **Tool System** - Extensible tools with auto-discovery
- **Subagent Delegation** - Specialized agents for complex tasks (Deep Agents pattern)
- **Rich TUI** - Beautiful terminal interface with syntax highlighting

## Quick Start

```bash
# Clone and setup
git clone https://github.com/your-repo/AgentTheo.git
cd AgentTheo
python3 -m venv .venv
source .venv/bin/activate

# Install dependencies
pip install -r requirements.txt

# Configure
cp .env.example .env
# Edit .env with your OpenRouter API key

# Run
python main.py
```

## Configuration

Create a `.env` file with:

```env
# Required
THEO_OPENROUTER_API_KEY=your_api_key_here

# Model (optional)
THEO_OPENROUTER_MODEL=arcee-ai/trinity-mini
THEO_OPENROUTER_EMBEDDING_MODEL=openai/text-embedding-3-large

# Memory (optional)
THEO_MEMORY_ENABLED=true
THEO_MEMORY_AUTO_RETRIEVE_ENABLED=true
THEO_MEMORY_AUTO_RETRIEVE_K=5
THEO_VECTORDB_PATH=~/.theo/vectordb/
```

## Usage

### Chat Commands

| Command | Shortcut | Description |
|---------|----------|-------------|
| `quit` | `Ctrl+C` | Exit |
| `clear` | `Ctrl+L` | Clear screen |
| `new` | `Ctrl+N` | New session |
| `toggle` | `Ctrl+T` | Toggle streaming mode |

### Built-in Tools

| Tool | Description |
|------|-------------|
| `store_memory` | Save information with semantic encoding |
| `search_memory` | Semantic search of stored memories |
| `forget_memory` | Delete memories by ID or query |
| `list_memories` | List recent memories |
| `memory_stats` | Memory system statistics |
| `calculator` | Evaluate math expressions |
| `get_current_time` | Get current date/time |
| `reverse_string` | Reverse a string |

### Built-in Subagents

| Subagent | Description |
|----------|-------------|
| `memory-analyst` | Deep analysis of stored memories |

## Extending Theo

### Creating Tools

Create a file in `src/tools/`:

```python
# src/tools/my_tools.py
from src.registry import theo_tool

@theo_tool
def greet(name: str) -> str:
    """Greet someone by name."""
    return f"Hello, {name}!"
```

Tools are auto-discovered on startup. Nested directories are supported:
```
src/tools/web/fetcher.py  # Also auto-discovered
```

### Creating Subagents

Create a file in `src/subagents/`:

```python
# src/subagents/researcher.py
from src.registry import theo_subagent, get_tools_by_name

researcher = theo_subagent(
    name="researcher",
    description="Deep research into topics using memory",
    system_prompt="""You are a research expert.
    Search memories thoroughly and synthesize findings.""",
    tools=get_tools_by_name("search_memory", "list_memories"),
    model="anthropic/claude-sonnet",  # Optional model override
)
```

The main agent invokes subagents via:
```
task(name="researcher", task="Research quantum computing trends")
```

## Project Structure

```
AgentTheo/
├── main.py              # Entry point
├── src/
│   ├── agent.py         # Core agent & chat loop
│   ├── registry.py      # Tool & subagent registry
│   ├── tools/           # Auto-discovered tools
│   ├── subagents/       # Auto-discovered subagents
│   ├── memory/          # Semantic memory system
│   │   ├── manager.py   # Memory CRUD operations
│   │   ├── config.py    # Memory configuration
│   │   └── embeddings.py # Vector embeddings
│   └── ui/              # Rich TUI components
│       ├── components.py # Panel builders
│       └── streaming.py  # Streaming interface
├── .env.example         # Environment template
└── models.json          # Supported models
```

## Architecture

```
┌─────────────────────────────────────────────────────────┐
│                      Main Agent                          │
│  ┌─────────┐  ┌─────────┐  ┌─────────┐  ┌─────────────┐ │
│  │  Tools  │  │ Memory  │  │   UI    │  │  Subagents  │ │
│  └────┬────┘  └────┬────┘  └────┬────┘  └──────┬──────┘ │
└───────┼────────────┼────────────┼──────────────┼────────┘
        │            │            │              │
   ┌────▼────┐  ┌────▼────┐  ┌────▼────┐   ┌─────▼─────┐
   │ Registry│  │ Qdrant  │  │  Rich   │   │ Delegated │
   │  Auto-  │  │ Vector  │  │Terminal │   │   Work    │
   │ Discover│  │   DB    │  │   UI    │   │ (Isolated)│
   └─────────┘  └─────────┘  └─────────┘   └───────────┘
```

**Key Patterns:**
- **Auto-Discovery** - Tools/subagents register on import
- **Decorator Registration** - `@theo_tool` for clean API
- **Singleton Managers** - One memory manager instance
- **Deep Agents** - Subagents isolate complex work, preventing context bloat

## Memory System

Theo uses Qdrant for semantic memory storage:

```python
# Store a memory
store_memory(content="User prefers Python", memory_type="general")

# Search memories
search_memory(query="programming preferences", k=5)

# Auto-retrieval happens automatically before each query
```

Memory types: `general`, `document`, `conversation`, `tool_output`

## Requirements

- Python 3.11+
- OpenRouter API key
- Dependencies: langchain, langgraph, qdrant-client, rich

## License

MIT
