"""
AgentTheo Source Package

This package contains the core agent implementation, tools, and subagents.

Tools are registered using the @theo_tool decorator.
Subagents are registered using the theo_subagent() function.

Both are automatically discovered from their respective packages.
"""

from src.registry import (
    # Tool registration
    theo_tool,
    get_registered_tools,
    get_tools_by_name,
    clear_tool_registry,
    # Subagent registration
    theo_subagent,
    get_registered_subagents,
    clear_subagent_registry,
    get_subagent_by_name,
    # Combined operations
    clear_all_registries,
    clear_registry,  # backward compat alias
    # Types
    SubagentConfig,
)

__all__ = [
    # Tools
    "theo_tool",
    "get_registered_tools",
    "get_tools_by_name",
    "clear_tool_registry",
    # Subagents
    "theo_subagent",
    "get_registered_subagents",
    "clear_subagent_registry",
    "get_subagent_by_name",
    "SubagentConfig",
    # Combined
    "clear_all_registries",
    "clear_registry",
]
