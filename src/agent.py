"""
Rich TUI Agent Chat Interface

A beautiful terminal interface for DeepAgent with tool call visualization,
streaming responses, and Claude Code-style presentation.
"""

import os
import json
from datetime import datetime
from typing import Any
from dotenv import load_dotenv
from langchain_openai import ChatOpenAI
from langchain_core.messages import AIMessage, ToolMessage, HumanMessage, AIMessageChunk
from pydantic import SecretStr

from rich.console import Console, Group
from rich.panel import Panel
from rich.markdown import Markdown
from rich.syntax import Syntax
from rich.live import Live
from rich.spinner import Spinner
from rich.table import Table
from rich.text import Text
from rich.box import ROUNDED, HEAVY, DOUBLE
from rich.style import Style
from rich.padding import Padding
from rich.rule import Rule

from deepagents import create_deep_agent
from src import tools  # noqa: F401
from src.registry import get_registered_tools

load_dotenv()

# =============================================================================
# Console Setup
# =============================================================================

console = Console()

# Style definitions
STYLES = {
    "user": Style(color="bright_cyan", bold=True),
    "assistant": Style(color="bright_green"),
    "tool_name": Style(color="bright_yellow", bold=True),
    "tool_input": Style(color="bright_blue"),
    "tool_output": Style(color="bright_magenta"),
    "error": Style(color="bright_red", bold=True),
    "info": Style(color="bright_white", dim=True),
    "success": Style(color="bright_green", bold=True),
    "thinking": Style(color="bright_yellow", italic=True),
}


# =============================================================================
# TUI Components
# =============================================================================

def create_header():
    """Create the application header."""
    grid = Table.grid(expand=True)
    grid.add_column(justify="left")
    grid.add_column(justify="right")
    
    title = Text("🤖 DeepAgent", style="bold bright_cyan")
    timestamp = Text(datetime.now().strftime("%H:%M:%S"), style="dim")
    
    grid.add_row(title, timestamp)
    return Panel(grid, box=ROUNDED, style="bright_blue")


def create_tool_call_panel(tool_name: str, tool_input: dict, status: str = "running") -> Panel:
    """Create a styled panel for tool calls like Claude Code."""
    # Tool header with icon
    icons = {
        "running": "⚡",
        "success": "✅", 
        "error": "❌",
    }
    icon = icons.get(status, "🔧")
    
    header = Text()
    header.append(f"{icon} ", style="bold")
    header.append(tool_name, style=STYLES["tool_name"])
    
    # Format input as JSON with syntax highlighting
    try:
        input_str = json.dumps(tool_input, indent=2, default=str)
        content = Syntax(input_str, "json", theme="monokai", line_numbers=False)
    except:
        content = Text(str(tool_input), style=STYLES["tool_input"])
    
    border_style = {
        "running": "bright_yellow",
        "success": "bright_green",
        "error": "bright_red",
    }.get(status, "bright_blue")
    
    return Panel(
        content,
        title=header,
        title_align="left",
        border_style=border_style,
        box=ROUNDED,
        padding=(0, 1),
    )


def create_tool_result_panel(tool_name: str, result: str, is_error: bool = False) -> Panel:
    """Create a panel for tool results."""
    icon = "❌" if is_error else "📤"
    
    header = Text()
    header.append(f"{icon} ", style="bold")
    header.append(f"{tool_name} result", style=STYLES["tool_output"])
    
    # Truncate long results
    display_result = result
    if len(result) > 1000:
        display_result = result[:1000] + "\n... (truncated)"
    
    # Try to detect and highlight code/JSON
    try:
        parsed = json.loads(result)
        content = Syntax(json.dumps(parsed, indent=2), "json", theme="monokai", line_numbers=False)
    except:
        content = Text(display_result, style="dim white")
    
    return Panel(
        content,
        title=header,
        title_align="left",
        border_style="bright_magenta" if not is_error else "bright_red",
        box=ROUNDED,
        padding=(0, 1),
    )


def create_thinking_spinner(message: str = "Thinking") -> Panel:
    """Create a thinking indicator with spinner."""
    spinner = Spinner("dots", text=Text(f" {message}...", style=STYLES["thinking"]))
    return Panel(spinner, box=ROUNDED, border_style="yellow", padding=(0, 1))


def create_user_message_panel(message: str) -> Panel:
    """Create a panel for user messages."""
    return Panel(
        Text(message, style=STYLES["user"]),
        title=Text("👤 You", style="bold bright_cyan"),
        title_align="left",
        border_style="bright_cyan",
        box=ROUNDED,
        padding=(0, 1),
    )


def create_assistant_panel(content: str) -> Panel:
    """Create a panel for assistant responses with markdown rendering."""
    try:
        md = Markdown(content, code_theme="monokai")
    except:
        md = Text(content)
    
    return Panel(
        md,
        title=Text("🤖 Assistant", style="bold bright_green"),
        title_align="left",
        border_style="bright_green",
        box=ROUNDED,
        padding=(0, 1),
    )


# =============================================================================
# Agent Setup
# =============================================================================

def create_agent():
    """Create and configure the DeepAgent with all registered tools."""
    api_key = os.getenv("THEO_OPENROUTER_API_KEY")
    model_name = os.getenv("THEO_OPENROUTER_MODEL", "anthropic/claude-sonnet-4-20250514")

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
Be concise but thorough in your responses."""

    agent = create_deep_agent(
        model=model,
        system_prompt=system_prompt,
        tools=get_registered_tools(),
    )
    
    return agent, model_name


# =============================================================================
# Streaming Chat with Rich TUI
# =============================================================================

def stream_chat_rich(agent, message: str):
    """Stream a response with rich TUI displaying tool calls."""
    collected_text = ""
    current_tool_calls = {}  # Track tool calls by ID
    displayed_tool_calls = set()
    displayed_tool_results = set()
    
    # Use multiple stream modes to capture both messages and state updates
    try:
        for chunk in agent.stream(
            {"messages": [{"role": "user", "content": message}]},
            stream_mode="values",  # Get full state to see tool calls
        ):
            messages = chunk.get("messages", [])
            
            for msg in messages:
                # Handle AI Messages with potential tool calls
                if isinstance(msg, AIMessage):
                    # Check for tool calls
                    if hasattr(msg, "tool_calls") and msg.tool_calls:
                        for tool_call in msg.tool_calls:
                            tc_id = tool_call.get("id", id(tool_call))
                            if tc_id not in displayed_tool_calls:
                                displayed_tool_calls.add(tc_id)
                                tool_name = tool_call.get("name", "unknown")
                                tool_args = tool_call.get("args", {})
                                
                                # Display tool call panel
                                console.print()
                                console.print(create_tool_call_panel(
                                    tool_name, 
                                    tool_args, 
                                    status="running"
                                ))
                    
                    # Collect text content
                    if msg.content and isinstance(msg.content, str):
                        if msg.content != collected_text:
                            collected_text = msg.content
                
                # Handle Tool Messages (results)
                elif isinstance(msg, ToolMessage):
                    msg_id = getattr(msg, "tool_call_id", id(msg))
                    if msg_id not in displayed_tool_results:
                        displayed_tool_results.add(msg_id)
                        tool_name = getattr(msg, "name", "tool")
                        is_error = getattr(msg, "status", "") == "error"
                        
                        console.print(create_tool_result_panel(
                            tool_name,
                            str(msg.content)[:500],  # Limit display
                            is_error=is_error
                        ))
        
        # Display final response
        if collected_text:
            console.print()
            console.print(create_assistant_panel(collected_text))
            
    except Exception as e:
        console.print(Panel(
            Text(f"Error: {e}", style=STYLES["error"]),
            title="Error",
            border_style="red"
        ))


def stream_chat_rich_v2(agent, message: str):
    """Alternative streaming with token-by-token display and tool visualization."""
    response_text = ""
    tool_calls_shown = set()
    tool_results_shown = set()
    
    console.print()
    
    # Start with a thinking indicator
    with console.status("[bold yellow]Thinking...", spinner="dots"):
        # Collect first chunk to see if we're doing tool calls
        first_chunk = None
        stream = agent.stream(
            {"messages": [{"role": "user", "content": message}]},
            stream_mode="messages",
        )
        
    # Now stream the response
    console.print(Text("🤖 ", style="bold bright_green"), end="")
    
    for chunk in agent.stream(
        {"messages": [{"role": "user", "content": message}]},
        stream_mode="messages",
    ):
        msg, metadata = chunk
        msg_type = getattr(msg, "type", None)
        
        # Handle streaming AI content
        if msg_type == "AIMessageChunk":
            content = getattr(msg, "content", "")
            
            # Check for tool calls in the chunk
            tool_call_chunks = getattr(msg, "tool_call_chunks", [])
            if tool_call_chunks:
                for tc in tool_call_chunks:
                    tc_name = tc.get("name")
                    if tc_name and tc_name not in tool_calls_shown:
                        tool_calls_shown.add(tc_name)
                        console.print()  # Newline before tool panel
                        console.print(create_tool_call_panel(
                            tc_name,
                            tc.get("args", {}),
                            status="running"
                        ))
            
            # Print text content
            if isinstance(content, str) and content:
                console.print(content, end="", style=STYLES["assistant"])
                response_text += content
            elif isinstance(content, list):
                for item in content:
                    if isinstance(item, dict) and item.get("type") == "text":
                        text = item.get("text", "")
                        console.print(text, end="", style=STYLES["assistant"])
                        response_text += text
        
        # Handle tool messages
        elif msg_type == "ToolMessage" or (hasattr(msg, "tool_call_id")):
            tc_id = getattr(msg, "tool_call_id", None)
            if tc_id and tc_id not in tool_results_shown:
                tool_results_shown.add(tc_id)
                console.print()  # Newline
                console.print(create_tool_result_panel(
                    getattr(msg, "name", "tool"),
                    str(getattr(msg, "content", ""))[:500],
                ))
    
    console.print()  # Final newline


# =============================================================================
# Main Chat Loop
# =============================================================================

def run_chat_loop():
    """Run the main chat loop with Rich TUI."""
    console.clear()
    console.print(create_header())
    console.print()
    
    try:
        agent, model_name = create_agent()
        tools_list = get_registered_tools()
    except Exception as e:
        console.print(Panel(
            Text(f"Failed to initialize: {e}", style=STYLES["error"]),
            title="Initialization Error",
            border_style="red"
        ))
        return
    
    # Show startup info
    info_grid = Table.grid(padding=(0, 2))
    info_grid.add_column(style="dim")
    info_grid.add_column(style="bright_white")
    info_grid.add_row("Model:", model_name)
    info_grid.add_row("Tools:", ", ".join([t.name for t in tools_list]))
    
    console.print(Panel(
        info_grid,
        title="[bold]Configuration[/]",
        border_style="dim",
        box=ROUNDED
    ))
    console.print()
    console.print(Text("Type 'quit' to exit, 'clear' to clear screen", style="dim"))
    console.print(Rule(style="dim"))
    
    while True:
        try:
            console.print()
            user_input = console.input("[bold bright_cyan]You:[/] ").strip()
            
            if not user_input:
                continue
            
            if user_input.lower() in ("quit", "exit", "q"):
                console.print(Panel("👋 Goodbye!", border_style="bright_blue"))
                break
            
            if user_input.lower() == "clear":
                console.clear()
                console.print(create_header())
                continue
            
            # Display user message in a panel for consistency
            # (Optional: comment out if you prefer inline display)
            # console.print(create_user_message_panel(user_input))
            
            # Stream the response with tool visualization
            stream_chat_rich(agent, user_input)
            
            console.print(Rule(style="dim"))
            
        except KeyboardInterrupt:
            console.print("\n")
            console.print(Panel("👋 Interrupted. Goodbye!", border_style="bright_yellow"))
            break
        except Exception as e:
            console.print(Panel(
                Text(f"Error: {e}", style=STYLES["error"]),
                border_style="red",
                title="Error"
            ))


if __name__ == "__main__":
    run_chat_loop()