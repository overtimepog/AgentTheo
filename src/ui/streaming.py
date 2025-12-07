"""
Streaming helpers for the Rich TUI experience.

Combines prior streaming variants into a single entry point. Supports
two modes via `token_stream` to choose chunked or value streaming.
"""

from typing import Callable, Optional

from langchain_core.messages import AIMessage, ToolMessage
from rich.panel import Panel
from rich.text import Text

from src.ui import (
    STYLES,
    console,
    create_assistant_panel,
    create_tool_call_panel,
    create_tool_result_panel,
    create_subagent_call_panel,
    create_subagent_result_panel,
)

# The Deep Agents library uses "task" as the tool name for subagent invocation
SUBAGENT_TOOL_NAME = "task"


def _get_memory_context(message: str, memory_getter: Optional[Callable]):
    """Fetch contextual memory text if available."""
    if not memory_getter:
        return ""
    memory_manager = memory_getter()
    if not memory_manager:
        return ""
    try:
        context = memory_manager.get_context(message)
        if context:
            console.print(Text("📚 Retrieved relevant memories", style="dim italic"))
        return context or ""
    except Exception:
        return ""


def stream_chat_rich(
    agent,
    message: str,
    thread_id: str,
    memory_getter: Optional[Callable] = None,
    token_stream: bool = False,
):
    """Stream a response with rich TUI displaying tool calls.

    token_stream=False uses value streaming (full messages).
    token_stream=True uses token-by-token streaming with a spinner.
    """

    config = {"configurable": {"thread_id": thread_id}}

    memory_context = _get_memory_context(message, memory_getter)
    full_message = f"{memory_context}\n\n[Current query]: {message}" if memory_context else message

    if not token_stream:
        collected_text = ""
        displayed_tool_calls = set()
        displayed_tool_results = set()
        # Track subagent calls by their tool_call_id -> subagent_name
        subagent_calls: dict[str, str] = {}

        try:
            for chunk in agent.stream(
                {"messages": [{"role": "user", "content": full_message}]},
                config=config,
                stream_mode="values",
            ):
                messages = chunk.get("messages", [])

                for msg in messages:
                    if isinstance(msg, AIMessage):
                        if hasattr(msg, "tool_calls") and msg.tool_calls:
                            for tool_call in msg.tool_calls:
                                tc_id = tool_call.get("id", id(tool_call))
                                if tc_id not in displayed_tool_calls:
                                    displayed_tool_calls.add(tc_id)
                                    tool_name = tool_call.get("name", "unknown")
                                    tool_args = tool_call.get("args", {})
                                    console.print()

                                    # Check if this is a subagent call
                                    if tool_name == SUBAGENT_TOOL_NAME:
                                        subagent_name = tool_args.get("name", "subagent")
                                        task_desc = tool_args.get("task", str(tool_args))
                                        subagent_calls[str(tc_id)] = subagent_name
                                        console.print(create_subagent_call_panel(
                                            subagent_name, task_desc, status="running"
                                        ))
                                    else:
                                        console.print(create_tool_call_panel(tool_name, tool_args, status="running"))

                        if msg.content and isinstance(msg.content, str):
                            if msg.content != collected_text:
                                collected_text = msg.content

                    elif isinstance(msg, ToolMessage):
                        msg_id = getattr(msg, "tool_call_id", id(msg))
                        if msg_id not in displayed_tool_results:
                            displayed_tool_results.add(msg_id)
                            tool_name = getattr(msg, "name", "tool")
                            is_error = getattr(msg, "status", "") == "error"

                            # Check if this result is from a subagent
                            if msg_id in subagent_calls:
                                subagent_name = subagent_calls[msg_id]
                                console.print(create_subagent_result_panel(
                                    subagent_name, str(msg.content), is_error=is_error
                                ))
                            else:
                                console.print(
                                    create_tool_result_panel(tool_name, str(msg.content)[:500], is_error=is_error)
                                )

            if collected_text:
                console.print()
                console.print(create_assistant_panel(collected_text))

        except Exception as e:
            console.print(Panel(Text(f"Error: {e}", style=STYLES["error"]), title="Error", border_style="red"))

        return

    # token_stream=True path
    response_text = ""
    tool_calls_shown = set()
    tool_results_shown = set()
    # Track subagent calls: tool_call_id -> subagent_name
    subagent_calls: dict[str, str] = {}

    console.print()

    with console.status("[bold yellow]Thinking...", spinner="dots"):
        pass

    console.print(Text("🤖 ", style="bold bright_green"), end="")

    for chunk in agent.stream(
        {"messages": [{"role": "user", "content": full_message}]},
        config=config,
        stream_mode="messages",
    ):
        msg, _ = chunk
        msg_type = getattr(msg, "type", None)

        if msg_type == "AIMessageChunk":
            content = getattr(msg, "content", "")

            tool_call_chunks = getattr(msg, "tool_call_chunks", [])
            if tool_call_chunks:
                for tc in tool_call_chunks:
                    tc_name = tc.get("name")
                    tc_id = tc.get("id")
                    tc_args = tc.get("args", {})

                    if tc_name and tc_name not in tool_calls_shown:
                        tool_calls_shown.add(tc_name)
                        console.print()

                        # Check if this is a subagent call
                        if tc_name == SUBAGENT_TOOL_NAME:
                            subagent_name = tc_args.get("name", "subagent") if isinstance(tc_args, dict) else "subagent"
                            task_desc = tc_args.get("task", str(tc_args)) if isinstance(tc_args, dict) else str(tc_args)
                            if tc_id:
                                subagent_calls[tc_id] = subagent_name
                            console.print(create_subagent_call_panel(
                                subagent_name, task_desc, status="running"
                            ))
                        else:
                            console.print(create_tool_call_panel(tc_name, tc_args, status="running"))

            if isinstance(content, str) and content:
                console.print(content, end="", style=STYLES["assistant"])
                response_text += content
            elif isinstance(content, list):
                for item in content:
                    if isinstance(item, dict) and item.get("type") == "text":
                        text = item.get("text", "")
                        console.print(text, end="", style=STYLES["assistant"])
                        response_text += text

        elif msg_type == "ToolMessage" or hasattr(msg, "tool_call_id"):
            tc_id = getattr(msg, "tool_call_id", None)
            if tc_id and tc_id not in tool_results_shown:
                tool_results_shown.add(tc_id)
                console.print()

                tool_name = getattr(msg, "name", "tool")
                content = str(getattr(msg, "content", ""))
                is_error = getattr(msg, "status", "") == "error"

                # Check if this result is from a subagent
                if tc_id in subagent_calls:
                    subagent_name = subagent_calls[tc_id]
                    console.print(create_subagent_result_panel(
                        subagent_name, content, is_error=is_error
                    ))
                else:
                    console.print(
                        create_tool_result_panel(tool_name, content[:500], is_error=is_error)
                    )

    console.print()
