"""
Rich TUI Agent Chat Interface

A beautiful terminal interface for DeepAgent with tool call visualization,
streaming responses, and Claude Code-style presentation.
"""

import os
import uuid
from dotenv import load_dotenv
from langchain_openai import ChatOpenAI
from langgraph.checkpoint.memory import InMemorySaver
from pydantic import SecretStr
from prompt_toolkit import PromptSession
from prompt_toolkit.key_binding import KeyBindings

from rich.box import ROUNDED
from rich.panel import Panel
from rich.table import Table
from rich.text import Text
from rich.rule import Rule

from deepagents import create_deep_agent
from src import tools  # noqa: F401
from src.registry import get_registered_tools
from src.memory import get_memory_manager, get_memory_config
from src.ui import STYLES, console, create_header, stream_chat_rich

load_dotenv()

# Initialize memory manager (lazy - won't connect until first use)
_memory_manager = None

def get_agent_memory_manager():
    """Get the memory manager instance for the agent."""
    global _memory_manager
    if _memory_manager is None:
        config = get_memory_config()
        if config.is_configured():
            _memory_manager = get_memory_manager()
    return _memory_manager

# =============================================================================
# Agent Setup & Session Management
# =============================================================================

# Global checkpointer for conversation persistence
_checkpointer = InMemorySaver()


def generate_thread_id() -> str:
    """Generate a unique thread ID for a new conversation session."""
    return str(uuid.uuid4())


def create_agent():
    """Create and configure the DeepAgent with all registered tools and memory."""
    api_key = os.getenv("THEO_OPENROUTER_API_KEY")
    model_name = os.getenv("THEO_OPENROUTER_MODEL", "anthropic/claude-sonnet-4-20250514")
    embedding_model = os.getenv("THEO_OPENROUTER_EMBEDDING_MODEL", "openai/text-embedding-3-large")

    if not api_key:
        raise ValueError("THEO_OPENROUTER_API_KEY not found in environment.")

    model = ChatOpenAI(
        model=model_name,
        api_key=SecretStr(api_key),
        base_url="https://openrouter.ai/api/v1",
        default_headers={"HTTP-Referer": "http://localhost"},
        streaming=True,
    )

    system_prompt = """You are a helpful AI assistant with access to various tools.
Use your planning capabilities to break down complex tasks into manageable steps.
When you learn something important about the user or task, consider storing it in memory.
Be concise but thorough in your responses.

IMPORTANT: When you need to use multiple tools where one depends on another's output,
call the first tool, wait for its result, then call the dependent tool with the actual value.
For example: First call get_current_time, then use its actual result in store_memory."""

    agent = create_deep_agent(
        model=model,
        system_prompt=system_prompt,
        tools=get_registered_tools(),
        checkpointer=_checkpointer
    )
    return agent, model_name, embedding_model


def build_prompt_session():
    """Configure a PromptSession with key bindings for common actions."""
    kb = KeyBindings()

    @kb.add("c-l")
    def _(event):
        event.app.exit(result="__clear__")

    @kb.add("c-n")
    def _(event):
        event.app.exit(result="__new__")

    @kb.add("c-t")
    def _(event):
        event.app.exit(result="__toggle_stream__")

    @kb.add("c-q")
    def _(event):
        event.app.exit(result="__quit__")

    return PromptSession(prompt_continuation="", key_bindings=kb)


# =============================================================================
# Main Chat Loop
# =============================================================================

def run_chat_loop():
    """Run the main chat loop with Rich TUI and persistent memory."""
    try:
        agent, model_name, embedding_model = create_agent()
        tools_list = get_registered_tools()
    except Exception as e:
        console.print(Panel(
            Text(f"Failed to initialize: {e}", style=STYLES["error"]),
            title="Initialization Error",
            border_style="red"
        ))
        return

    thread_id = generate_thread_id()
    token_stream_mode = True

    def show_header():
        console.clear()
        console.print(create_header())

    def refresh_session_banner():
        # Initialize memory system
        memory_manager = get_agent_memory_manager()
        memory_status = "Enabled" if memory_manager else "Disabled"
        if memory_manager:
            try:
                memory_manager.initialize()
                stats = memory_manager.get_stats()
                memory_count = stats.get("total_memories", 0)
                memory_status = f"Enabled ({memory_count} memories)"
            except Exception:
                memory_status = "Error initializing"

        info_grid = Table.grid(padding=(0, 2))
        info_grid.add_column(style="dim")
        info_grid.add_column(style="bright_white")
        info_grid.add_row("Agent Model:", model_name)
        info_grid.add_row("Embedding Model:", embedding_model)
        info_grid.add_row("Tools:", ", ".join([t.name for t in tools_list]))
        info_grid.add_row("Memory:", memory_status)
        info_grid.add_row("Session:", thread_id[:8] + "...")
        info_grid.add_row("Token Stream:", "On" if token_stream_mode else "Off")

        console.print(Panel(
            info_grid,
            title="[bold]Configuration[/]",
            border_style="dim",
            box=ROUNDED
        ))
        console.print()
        console.print(Text("Ctrl+C quit | Ctrl+L clear | Ctrl+N new session | Ctrl+T toggle token stream", style="dim"))
        console.print(Text("Type 'quit', 'clear', 'new', or 'toggle' also works.", style="dim"))
        console.print(Rule(style="dim"))

    show_header()
    refresh_session_banner()

    def handle_clear():
        show_header()
        refresh_session_banner()

    def handle_new_session():
        nonlocal thread_id
        thread_id = generate_thread_id()
        console.print(Panel(Text(f"Started new session: {thread_id[:8]}...", style="bright_green"), border_style="green"))
        refresh_session_banner()

    def handle_toggle_stream():
        nonlocal token_stream_mode
        token_stream_mode = not token_stream_mode
        console.print(Panel(Text(f"Token stream {'enabled' if token_stream_mode else 'disabled'}.", style="bright_cyan"), border_style="cyan"))
        refresh_session_banner()

    def handle_quit():
        console.print(Panel("👋 Goodbye!", border_style="bright_blue"))

    session = build_prompt_session()

    while True:
        try:
            console.print()
            user_input = session.prompt("You: ")

            if not user_input:
                continue

            if user_input == "__quit__" or user_input.lower() in ("quit", "exit", "q"):
                handle_quit()
                break

            if user_input == "__clear__" or user_input.lower() == "clear":
                handle_clear()
                continue

            if user_input == "__new__" or user_input.lower() == "new":
                handle_new_session()
                continue

            if user_input == "__toggle_stream__" or user_input.lower() == "toggle":
                handle_toggle_stream()
                continue

            stream_chat_rich(
                agent,
                user_input,
                thread_id,
                memory_getter=get_agent_memory_manager,
                token_stream=token_stream_mode,
            )

            console.print(Rule(style="dim"))
            
        except KeyboardInterrupt:
            console.print("\n")
            console.print(Panel("👋 Interrupted. Goodbye!", border_style="bright_yellow"))
            break
        except EOFError:
            handle_quit()
            break
        except Exception as e:
            console.print(Panel(
                Text(f"Error: {e}", style=STYLES["error"]),
                border_style="red",
                title="Error"
            ))


if __name__ == "__main__":
    run_chat_loop()