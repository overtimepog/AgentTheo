"""
Tool & Subagent Registry

Central registry for agent tools and subagents. The @theo_tool decorator
automatically registers functions as tools, and theo_subagent() registers
subagent configurations that can be used by the main agent.

Subagents follow the LangChain Deep Agents pattern where they are specialized
agents that can be delegated work from the main agent.
"""

from typing import Callable, TypedDict, Optional
from langchain_core.tools import BaseTool, tool as langchain_tool


# =============================================================================
# Type Definitions
# =============================================================================

class SubagentConfigRequired(TypedDict):
    """Required fields for a subagent configuration."""
    name: str
    description: str
    system_prompt: str


class SubagentConfig(SubagentConfigRequired, total=False):
    """Configuration for a subagent following the Deep Agents pattern.

    Required fields:
        name: Unique identifier for the subagent (used when calling task())
        description: Specific, action-oriented purpose description
        system_prompt: Detailed instructions including tool guidance

    Optional fields:
        tools: List of tool names or BaseTool instances for this subagent
        model: Override the main agent's model (e.g., "anthropic/claude-sonnet")
        middleware: Custom behavior, logging, rate limiting configurations
    """
    tools: list
    model: str
    middleware: list


# =============================================================================
# Tool Registry
# =============================================================================

_tool_registry: list[BaseTool] = []


def theo_tool(func: Callable) -> BaseTool:
    """
    Decorator to register a function as an agent tool.

    Usage:
        from src.registry import theo_tool

        @theo_tool
        def my_tool(param: str) -> str:
            '''Tool description goes here.'''
            return "result"
    """
    wrapped = langchain_tool(func)
    _tool_registry.append(wrapped)
    return wrapped


def get_registered_tools() -> list[BaseTool]:
    """Get all tools registered with @theo_tool decorator."""
    return _tool_registry.copy()


def get_tools_by_name(*names: str) -> list[BaseTool]:
    """Get specific tools by their names.

    Useful for subagent definitions that need a subset of available tools.

    Usage:
        from src.registry import theo_subagent, get_tools_by_name

        analyst = theo_subagent(
            name="analyst",
            description="Analyzes data",
            system_prompt="You analyze data.",
            tools=get_tools_by_name("search_memory", "list_memories"),
        )

    Args:
        *names: Tool names to retrieve

    Returns:
        List of matching BaseTool instances
    """
    name_set = set(names)
    return [t for t in _tool_registry if t.name in name_set]


def clear_tool_registry() -> None:
    """Clear all registered tools. Useful for testing."""
    _tool_registry.clear()


# Backward compatibility alias
def clear_registry() -> None:
    """Clear all registered tools. Alias for clear_tool_registry()."""
    clear_tool_registry()


# =============================================================================
# Subagent Registry
# =============================================================================

_subagent_registry: list[SubagentConfig] = []


def theo_subagent(
    name: str,
    description: str,
    system_prompt: str,
    tools: Optional[list] = None,
    model: Optional[str] = None,
    middleware: Optional[list] = None,
) -> SubagentConfig:
    """
    Register a subagent configuration for use by the main agent.

    Subagents are specialized agents that handle delegated work from the main
    agent, solving the "context bloat problem" by isolating detailed work.

    The main agent can invoke subagents via the task() tool:
        task(name="research-agent", task="Research quantum computing trends")

    Usage:
        from src.registry import theo_subagent

        # Register a research subagent
        research_agent = theo_subagent(
            name="research-agent",
            description="Used to research in-depth questions",
            system_prompt="You are a great researcher. Provide comprehensive answers.",
            tools=["search_memory", "web_search"],  # Optional: subset of tools
            model="anthropic/claude-sonnet",  # Optional: override model
        )

    Args:
        name: Unique identifier for the subagent (used when calling task())
        description: Specific, action-oriented description of what this subagent does.
                    This helps the main agent decide when to delegate.
        system_prompt: Detailed instructions for the subagent including:
                      - Its role and capabilities
                      - How to use its tools
                      - Output formatting requirements
        tools: Optional list of tool names or BaseTool instances.
               If None, subagent gets access to all main agent tools.
        model: Optional model override (e.g., "anthropic/claude-sonnet").
               If None, uses the main agent's model.
        middleware: Optional list of middleware configurations.

    Returns:
        The registered SubagentConfig dictionary.
    """
    config: SubagentConfig = {
        "name": name,
        "description": description,
        "system_prompt": system_prompt,
    }

    if tools is not None:
        config["tools"] = tools
    if model is not None:
        config["model"] = model
    if middleware is not None:
        config["middleware"] = middleware

    _subagent_registry.append(config)
    return config


def get_registered_subagents() -> list[SubagentConfig]:
    """Get all subagents registered with theo_subagent()."""
    return _subagent_registry.copy()


def clear_subagent_registry() -> None:
    """Clear all registered subagents. Useful for testing."""
    _subagent_registry.clear()


def get_subagent_by_name(name: str) -> Optional[SubagentConfig]:
    """Get a specific subagent by its name."""
    for subagent in _subagent_registry:
        if subagent.get("name") == name:
            return subagent
    return None


# =============================================================================
# Combined Registry Operations
# =============================================================================

def clear_all_registries() -> None:
    """Clear both tool and subagent registries. Useful for testing."""
    clear_tool_registry()
    clear_subagent_registry()
