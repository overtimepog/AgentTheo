"""LangGraph agent implementation for Theo Agent.

This module provides the core agent graph that orchestrates LLM reasoning,
tool execution, and response generation using the ReAct pattern.
"""

from typing import TYPE_CHECKING

from langchain_openai import ChatOpenAI
from langgraph.prebuilt import create_react_agent

from theo.agent.prompts import SYSTEM_PROMPT
from theo.agent.state import AgentState
from theo.tools import create_tools

if TYPE_CHECKING:
    from langgraph.graph.state import CompiledStateGraph

    from theo.config import Settings
    from theo.container.manager import ContainerManager


def create_agent(
    container_manager: "ContainerManager",
    config: "Settings",
) -> "CompiledStateGraph":
    """Create a configured Theo agent.

    This factory function creates a ReAct-style agent that can reason about
    security research tasks and execute tools in an isolated Kali container.
    The agent uses OpenRouter for LLM inference and supports streaming.

    Args:
        container_manager: Container manager instance for tool access.
                          Must be started before agent invocation.
        config: Application configuration containing OpenRouter settings.

    Returns:
        A compiled LangGraph state graph that can be invoked with:
        - `agent.invoke({"messages": [...]})` for synchronous execution
        - `agent.astream({"messages": [...]}, stream_mode="messages")`
          for streaming execution

    Example:
        >>> from theo.config import Settings
        >>> from theo.container.manager import ContainerManager
        >>>
        >>> config = Settings()
        >>> async with ContainerManager() as manager:
        ...     agent = create_agent(manager, config)
        ...     async for msg, metadata in agent.astream(
        ...         {"messages": [HumanMessage(content="Run whoami")]},
        ...         stream_mode="messages"
        ...     ):
        ...         print(msg.content)

    Note:
        The agent uses the system prompt defined in `prompts.py` to establish
        its security researcher persona and tool usage guidelines.
    """
    # Create OpenRouter-compatible LLM client
    # ChatOpenAI works with OpenRouter via custom base URL
    llm = ChatOpenAI(
        model=config.openrouter_model,
        api_key=config.openrouter_api_key,
        base_url=config.openrouter_base_url,
        default_headers={
            "HTTP-Referer": "https://theo-agent.local",
            "X-Title": "Theo Agent",
        },
        streaming=True,
    )

    # Create tools with container manager access
    tools = create_tools(container_manager)

    # Create ReAct agent using LangGraph's prebuilt helper
    # The agent alternates between reasoning (LLM) and acting (tools)
    agent = create_react_agent(
        model=llm,
        tools=tools,
        state_schema=AgentState,
        prompt=SYSTEM_PROMPT,
    )

    return agent
