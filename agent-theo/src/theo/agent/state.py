"""Agent state model for Theo Agent.

This module defines the state schema used by the LangGraph agent to track
conversation history and other stateful information during agent execution.
"""

from langgraph.prebuilt.chat_agent_executor import AgentState as PrebuiltAgentState


class AgentState(PrebuiltAgentState):
    """State for the Theo security assistant agent.

    This state class extends the prebuilt AgentState from LangGraph, which
    includes all required fields for create_react_agent:

    - messages: List of conversation messages with add_messages reducer
    - remaining_steps: Managed field tracking steps until recursion limit
    - is_last_step: Managed field indicating if at recursion limit

    The prebuilt AgentState handles all the necessary state management
    for the ReAct agent pattern automatically.

    Example:
        >>> from langchain_core.messages import HumanMessage, AIMessage
        >>> state = AgentState(messages=[
        ...     HumanMessage(content="Hello"),
        ...     AIMessage(content="Hi! How can I help?"),
        ... ])
        >>> len(state["messages"])
        2
    """

    pass  # PrebuiltAgentState has all required fields including remaining_steps
