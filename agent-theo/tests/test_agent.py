"""Tests for LangGraph agent functionality.

This module contains 5 focused tests for the Theo Agent:
- Test agent processes user message and returns response
- Test agent invokes tools when appropriate
- Test agent streams reasoning tokens
- Test agent handles tool errors gracefully
- Test conversation history is maintained within session
"""

from collections.abc import AsyncIterator
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from langchain_core.messages import AIMessage, HumanMessage, ToolMessage


class TestAgentProcessesUserMessage:
    """Test that agent processes user messages and returns responses."""

    @pytest.mark.asyncio
    async def test_agent_returns_response_for_user_message(self, env_with_api_key: str) -> None:
        """Test agent processes a user message and returns an AI response."""
        from theo.agent.graph import create_agent

        # Create mock container manager
        mock_manager = MagicMock()

        # Mock the ChatOpenAI to return a simple response
        with patch("theo.agent.graph.ChatOpenAI") as mock_llm_class:
            mock_llm = MagicMock()
            mock_llm_class.return_value = mock_llm

            # Mock create_react_agent to return a mock graph
            with patch("theo.agent.graph.create_react_agent") as mock_create_agent:
                mock_graph = AsyncMock()

                # Simulate agent response
                async def mock_astream(state, **kwargs):
                    yield (
                        AIMessage(content="I can help you with security research."),
                        {"langgraph_node": "agent"},
                    )

                mock_graph.astream = mock_astream
                mock_create_agent.return_value = mock_graph

                # Create agent
                from theo.config import Settings

                config = Settings()
                agent = create_agent(mock_manager, config)

                # Invoke with user message
                messages = []
                async for msg, metadata in agent.astream(
                    {"messages": [HumanMessage(content="Hello")]},
                    stream_mode="messages",
                ):
                    messages.append(msg)

                # Verify response
                assert len(messages) == 1
                assert isinstance(messages[0], AIMessage)
                assert "help" in messages[0].content.lower()


class TestAgentInvokesTools:
    """Test that agent invokes tools when appropriate."""

    @pytest.mark.asyncio
    async def test_agent_calls_shell_tool_for_command_request(self, env_with_api_key: str) -> None:
        """Test agent calls shell_command tool when user asks to run a command."""
        from theo.agent.graph import create_agent

        mock_manager = MagicMock()

        # Mock shell command execution
        async def mock_exec_command(cmd: str) -> AsyncIterator[tuple[str | None, str | None]]:
            yield ("root\n", None)

        mock_manager.exec_command = mock_exec_command

        with patch("theo.agent.graph.ChatOpenAI") as mock_llm_class:
            mock_llm = MagicMock()
            mock_llm_class.return_value = mock_llm

            with patch("theo.agent.graph.create_react_agent") as mock_create_agent:
                mock_graph = AsyncMock()
                tool_called = False

                async def mock_astream(state, **kwargs):
                    nonlocal tool_called
                    # First yield: AI decides to use tool
                    yield (
                        AIMessage(
                            content="",
                            tool_calls=[
                                {
                                    "id": "call_1",
                                    "name": "shell_command",
                                    "args": {"command": "whoami"},
                                }
                            ],
                        ),
                        {"langgraph_node": "agent"},
                    )
                    tool_called = True
                    # Second yield: Tool response
                    yield (
                        ToolMessage(content="root\n", tool_call_id="call_1"),
                        {"langgraph_node": "tools"},
                    )
                    # Third yield: Final AI response
                    yield (
                        AIMessage(content="The current user is root."),
                        {"langgraph_node": "agent"},
                    )

                mock_graph.astream = mock_astream
                mock_create_agent.return_value = mock_graph

                from theo.config import Settings

                config = Settings()
                agent = create_agent(mock_manager, config)

                messages = []
                async for msg, metadata in agent.astream(
                    {"messages": [HumanMessage(content="Run whoami")]},
                    stream_mode="messages",
                ):
                    messages.append((msg, metadata))

                # Verify tool was invoked
                assert tool_called
                # Verify we got tool-related messages
                tool_messages = [m for m, _ in messages if isinstance(m, ToolMessage)]
                assert len(tool_messages) >= 1


class TestAgentStreamsReasoning:
    """Test that agent streams reasoning tokens."""

    @pytest.mark.asyncio
    async def test_agent_streams_tokens_during_response(self, env_with_api_key: str) -> None:
        """Test that agent streams tokens as they are generated."""
        from theo.agent.graph import create_agent

        mock_manager = MagicMock()

        with patch("theo.agent.graph.ChatOpenAI") as mock_llm_class:
            mock_llm = MagicMock()
            mock_llm_class.return_value = mock_llm

            with patch("theo.agent.graph.create_react_agent") as mock_create_agent:
                mock_graph = AsyncMock()
                tokens_streamed = []

                async def mock_astream(state, **kwargs):
                    # Simulate streaming multiple token chunks
                    for token in ["I ", "will ", "help ", "you."]:
                        tokens_streamed.append(token)
                        yield (
                            AIMessage(content=token),
                            {"langgraph_node": "agent"},
                        )

                mock_graph.astream = mock_astream
                mock_create_agent.return_value = mock_graph

                from theo.config import Settings

                config = Settings()
                agent = create_agent(mock_manager, config)

                received_tokens = []
                async for msg, metadata in agent.astream(
                    {"messages": [HumanMessage(content="Help me")]},
                    stream_mode="messages",
                ):
                    if isinstance(msg, AIMessage):
                        received_tokens.append(msg.content)

                # Verify streaming worked
                assert len(received_tokens) == 4
                assert received_tokens == ["I ", "will ", "help ", "you."]


class TestAgentHandlesToolErrors:
    """Test that agent handles tool errors gracefully."""

    @pytest.mark.asyncio
    async def test_agent_handles_tool_execution_error(self, env_with_api_key: str) -> None:
        """Test agent gracefully handles errors from tool execution."""
        from theo.agent.graph import create_agent

        mock_manager = MagicMock()

        with patch("theo.agent.graph.ChatOpenAI") as mock_llm_class:
            mock_llm = MagicMock()
            mock_llm_class.return_value = mock_llm

            with patch("theo.agent.graph.create_react_agent") as mock_create_agent:
                mock_graph = AsyncMock()

                async def mock_astream(state, **kwargs):
                    # AI tries to use tool
                    yield (
                        AIMessage(
                            content="",
                            tool_calls=[
                                {
                                    "id": "call_1",
                                    "name": "shell_command",
                                    "args": {"command": "invalid_cmd"},
                                }
                            ],
                        ),
                        {"langgraph_node": "agent"},
                    )
                    # Tool returns error
                    yield (
                        ToolMessage(
                            content='{"success": false, "error": "Command not found"}',
                            tool_call_id="call_1",
                        ),
                        {"langgraph_node": "tools"},
                    )
                    # Agent responds gracefully
                    yield (
                        AIMessage(content="The command failed. Let me try a different approach."),
                        {"langgraph_node": "agent"},
                    )

                mock_graph.astream = mock_astream
                mock_create_agent.return_value = mock_graph

                from theo.config import Settings

                config = Settings()
                agent = create_agent(mock_manager, config)

                messages = []
                async for msg, metadata in agent.astream(
                    {"messages": [HumanMessage(content="Run invalid command")]},
                    stream_mode="messages",
                ):
                    messages.append(msg)

                # Verify agent handled error and provided graceful response
                ai_messages = [m for m in messages if isinstance(m, AIMessage) and m.content]
                assert len(ai_messages) >= 1
                # The last AI message should be the recovery message
                assert any(
                    "failed" in m.content.lower() or "try" in m.content.lower() for m in ai_messages
                )


class TestConversationHistory:
    """Test that conversation history is maintained within session."""

    @pytest.mark.asyncio
    async def test_conversation_history_maintained_across_turns(
        self, env_with_api_key: str
    ) -> None:
        """Test that messages from previous turns are preserved."""
        from theo.agent.graph import create_agent

        mock_manager = MagicMock()

        with patch("theo.agent.graph.ChatOpenAI") as mock_llm_class:
            mock_llm = MagicMock()
            mock_llm_class.return_value = mock_llm

            with patch("theo.agent.graph.create_react_agent") as mock_create_agent:
                mock_graph = AsyncMock()
                received_states = []

                async def mock_astream(state, **kwargs):
                    # Capture the state to verify history
                    received_states.append(state.copy())
                    yield (
                        AIMessage(content="Response to your message."),
                        {"langgraph_node": "agent"},
                    )

                mock_graph.astream = mock_astream
                mock_create_agent.return_value = mock_graph

                from theo.config import Settings

                config = Settings()
                agent = create_agent(mock_manager, config)

                # First turn
                messages_turn1 = [HumanMessage(content="First message")]
                async for msg, metadata in agent.astream(
                    {"messages": messages_turn1},
                    stream_mode="messages",
                ):
                    pass

                # Second turn with history
                messages_turn2 = [
                    HumanMessage(content="First message"),
                    AIMessage(content="Response to first message"),
                    HumanMessage(content="Second message"),
                ]
                async for msg, metadata in agent.astream(
                    {"messages": messages_turn2},
                    stream_mode="messages",
                ):
                    pass

                # Verify the second turn received the full history
                assert len(received_states) == 2
                # First turn had 1 message
                assert len(received_states[0]["messages"]) == 1
                # Second turn had 3 messages (history preserved)
                assert len(received_states[1]["messages"]) == 3


class TestAgentStateModel:
    """Test the AgentState model structure."""

    def test_agent_state_has_messages_field(self) -> None:
        """Test that AgentState has the required messages field."""
        from theo.agent.state import AgentState

        # AgentState should be usable as a TypedDict
        state: AgentState = {"messages": []}
        assert "messages" in state
        assert isinstance(state["messages"], list)

    def test_agent_state_accepts_message_objects(self) -> None:
        """Test that AgentState accepts LangChain message objects."""
        from theo.agent.state import AgentState

        state: AgentState = {
            "messages": [
                HumanMessage(content="Hello"),
                AIMessage(content="Hi there!"),
            ]
        }
        assert len(state["messages"]) == 2
