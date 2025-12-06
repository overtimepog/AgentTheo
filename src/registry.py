"""
Tool Registry

Central registry for agent tools. The @agent_tool decorator automatically
registers functions as tools that can be used by the agent.
"""

from typing import Callable
from langchain_core.tools import BaseTool, tool as langchain_tool

# =============================================================================
# Tool Registry
# =============================================================================

_tool_registry: list = []


def agent_tool(func: Callable) -> BaseTool:
    """
    Decorator to register a function as an agent tool.
    
    Usage:
        from src.registry import agent_tool
        
        @agent_tool
        def my_tool(param: str) -> str:
            '''Tool description goes here.'''
            return "result"
    """
    # Wrap with LangChain's tool decorator
    wrapped = langchain_tool(func)
    # Add to registry
    _tool_registry.append(wrapped)
    return wrapped


def get_registered_tools() -> list:
    """Get all tools registered with @agent_tool decorator."""
    return _tool_registry.copy()


def clear_registry() -> None:
    """Clear all registered tools. Useful for testing."""
    _tool_registry.clear()
