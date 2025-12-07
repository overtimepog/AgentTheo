"""
Rich TUI components for AgentTheo.

This module centralizes console styling and panel builders so the
interactive agent UI can be reused across entry points.
"""

import json
from datetime import datetime

from rich.console import Console
from rich.markdown import Markdown
from rich.panel import Panel
from rich.spinner import Spinner
from rich.syntax import Syntax
from rich.table import Table
from rich.text import Text
from rich.box import ROUNDED
from rich.style import Style

console = Console()

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


def create_header() -> Panel:
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
    icons = {
        "running": "⚡",
        "success": "✅",
        "error": "❌",
    }
    icon = icons.get(status, "🔧")

    header = Text()
    header.append(f"{icon} ", style="bold")
    header.append(tool_name, style=STYLES["tool_name"])

    try:
        input_str = json.dumps(tool_input, indent=2, default=str)
        content = Syntax(input_str, "json", theme="monokai", line_numbers=False)
    except Exception:
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

    display_result = result
    if len(result) > 1000:
        display_result = result[:1000] + "\n... (truncated)"

    try:
        parsed = json.loads(result)
        content = Syntax(json.dumps(parsed, indent=2), "json", theme="monokai", line_numbers=False)
    except Exception:
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
    except Exception:
        md = Text(content)

    return Panel(
        md,
        title=Text("🤖 Assistant", style="bold bright_green"),
        title_align="left",
        border_style="bright_green",
        box=ROUNDED,
        padding=(0, 1),
    )
