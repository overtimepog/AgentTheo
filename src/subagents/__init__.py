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
from pathlib import Path


def discover_subagents() -> None:
    """
    Automatically import all Python modules in the subagents directory and subdirectories.

    This triggers the theo_subagent() calls for each subagent definition,
    registering them in the global subagent registry.

    Supports nested directories like:
        - src/subagents/my_agent.py -> src.subagents.my_agent
        - src/subagents/research/deep_agent.py -> src.subagents.research.deep_agent
    """
    package_dir = Path(__file__).parent

    # Find all .py files recursively
    for py_file in package_dir.rglob("*.py"):
        # Skip private modules (starting with _)
        if py_file.name.startswith("_"):
            continue

        # Convert file path to module path
        # e.g., /path/to/src/subagents/research/deep_agent.py -> src.subagents.research.deep_agent
        relative_path = py_file.relative_to(package_dir.parent.parent)
        module_path = str(relative_path.with_suffix("")).replace("/", ".").replace("\\", ".")

        # Import the module, which triggers theo_subagent() calls
        try:
            importlib.import_module(module_path)
        except Exception as e:
            # Log but don't fail on individual module import errors
            import logging
            logging.getLogger(__name__).warning(
                f"Failed to import subagent module '{module_path}': {e}"
            )


# Auto-discover subagents when this package is imported
discover_subagents()
