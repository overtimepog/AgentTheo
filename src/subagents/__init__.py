"""
Subagents Package

This package automatically discovers and loads all subagents from Python files
in this directory. Simply create a new .py file with theo_subagent() calls
and they will be automatically registered.

Subagents follow the LangChain Deep Agents pattern - they are specialized agents
that handle delegated work from the main agent, solving the "context bloat problem"
by isolating detailed work so the main agent receives only final results.

Example:
    # src/subagents/research_agent.py
    from src.registry import theo_subagent

    research_agent = theo_subagent(
        name="research-agent",
        description="Used to research in-depth questions about any topic",
        system_prompt='''You are a thorough research assistant.
        When given a query:
        1. Search available memory for relevant context
        2. Synthesize information into a comprehensive answer
        3. Keep responses under 500 words unless more detail is requested
        ''',
        tools=["search_memory", "list_memories"],  # Optional: specific tools
        model="anthropic/claude-sonnet",  # Optional: model override
    )

Usage in main agent:
    The main agent can invoke subagents via the task() tool:
    task(name="research-agent", task="Research the history of neural networks")

Key concepts:
    - name: Unique identifier (used when calling task())
    - description: Helps main agent decide when to delegate
    - system_prompt: Detailed instructions for the subagent
    - tools: Optional subset of tools (defaults to all main agent tools)
    - model: Optional model override
"""

import importlib
import pkgutil
from pathlib import Path


def discover_subagents() -> None:
    """
    Automatically import all Python modules in the subagents directory.

    This triggers the theo_subagent() calls for each subagent definition,
    registering them in the global subagent registry.
    """
    package_dir = Path(__file__).parent

    for module_info in pkgutil.iter_modules([str(package_dir)]):
        if module_info.name.startswith("_"):
            # Skip private modules like __init__
            continue

        # Import the module, which triggers theo_subagent() calls
        importlib.import_module(f"src.subagents.{module_info.name}")


# Auto-discover subagents when this package is imported
discover_subagents()
