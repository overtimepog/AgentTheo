"""Agent module for LangGraph-based ReAct agent.

This module provides the core agent functionality for Theo, including
the agent graph, state model, and system prompts.

Usage:
    >>> from theo.agent import create_agent
    >>> from theo.config import Settings
    >>> from theo.container.manager import ContainerManager
    >>>
    >>> config = Settings()
    >>> async with ContainerManager() as manager:
    ...     agent = create_agent(manager, config)
    ...     # Use agent.astream() for streaming responses
"""

from theo.agent.graph import create_agent
from theo.agent.prompts import SYSTEM_PROMPT
from theo.agent.state import AgentState

__all__ = [
    "create_agent",
    "AgentState",
    "SYSTEM_PROMPT",
]
