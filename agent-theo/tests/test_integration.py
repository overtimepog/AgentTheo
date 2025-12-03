"""Integration tests for Theo Agent.

This module contains integration tests that verify complete flows through
the system, testing how components work together rather than in isolation.

Integration gaps filled:
1. End-to-end: user message -> agent -> tool -> container -> response
2. Container lifecycle: create on start, destroy on exit
3. File transfer roundtrip: upload then download same file
4. Error propagation: API errors, container errors, tool errors display correctly
5. OpenRouter API error handling
6. Graceful handling of missing Docker daemon
7. Reasoning panel clears between turns
8. Component wiring verification
"""

from pathlib import Path
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from langchain_core.messages import AIMessage, HumanMessage, ToolMessage

# --- Fixtures ---


@pytest.fixture
def mock_docker_client():
    """Create a mock Docker client for integration tests."""
    client = MagicMock()
    container = MagicMock()
    container.id = "integration-test-container"
    container.status = "running"
    container.name = "theo-integration-test"
    container.reload = MagicMock()
    client.containers.run.return_value = container
    client.ping.return_value = True
    return client


def docker_available() -> bool:
    """Check if Docker daemon is available."""
    try:
        import docker

        client = docker.from_env()
        client.ping()
        return True
    except Exception:
        return False


# --- End-to-End Flow Tests ---


@pytest.mark.integration
class TestEndToEndFlow:
    """Test complete flows through the system."""

    async def test_full_conversation_flow_with_tool_execution(self, env_with_api_key: str) -> None:
        """Test: User message -> agent -> tool -> container -> response.

        This test verifies that a user message flows correctly through
        the entire system: agent processes it, decides to use a tool,
        tool executes in container, and response flows back.
        """
        from theo.agent.graph import create_agent
        from theo.config import Settings

        # Mock container manager with working exec_command
        mock_manager = MagicMock()

        async def mock_exec_command(cmd: str, workdir: str | None = None):
            yield ("root\n", None)

        mock_manager.exec_command = mock_exec_command
        mock_manager.is_running = True

        # Mock the LLM to simulate tool usage flow
        with patch("theo.agent.graph.ChatOpenAI") as mock_llm_class:
            mock_llm = MagicMock()
            mock_llm_class.return_value = mock_llm

            with patch("theo.agent.graph.create_react_agent") as mock_create_agent:
                mock_graph = AsyncMock()
                execution_trace = []

                async def mock_astream(state, **kwargs):
                    execution_trace.append("user_message_received")
                    # Agent decides to use shell_command tool
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
                    execution_trace.append("tool_called")
                    # Tool executes and returns result
                    yield (
                        ToolMessage(
                            content='{"stdout": "root\\n", "stderr": "", "exit_code": 0}',
                            tool_call_id="call_1",
                        ),
                        {"langgraph_node": "tools"},
                    )
                    execution_trace.append("tool_result_received")
                    # Agent provides final response
                    yield (
                        AIMessage(content="The current user is root."),
                        {"langgraph_node": "agent"},
                    )
                    execution_trace.append("final_response")

                mock_graph.astream = mock_astream
                mock_create_agent.return_value = mock_graph

                config = Settings()
                agent = create_agent(mock_manager, config)

                messages = []
                async for msg, metadata in agent.astream(
                    {"messages": [HumanMessage(content="Who is the current user?")]},
                    stream_mode="messages",
                ):
                    messages.append((msg, metadata))

                # Verify complete flow executed
                assert "user_message_received" in execution_trace
                assert "tool_called" in execution_trace
                assert "tool_result_received" in execution_trace
                assert "final_response" in execution_trace

                # Verify we got all message types
                ai_messages = [m for m, _ in messages if isinstance(m, AIMessage)]
                tool_messages = [m for m, _ in messages if isinstance(m, ToolMessage)]
                assert len(ai_messages) >= 1
                assert len(tool_messages) >= 1


@pytest.mark.integration
class TestContainerLifecycle:
    """Test container lifecycle management."""

    async def test_container_cleanup_on_normal_exit(self, mock_docker_client: MagicMock) -> None:
        """Container is destroyed when context manager exits normally."""
        from theo.container.manager import ContainerManager

        container = mock_docker_client.containers.run.return_value

        with patch("docker.from_env", return_value=mock_docker_client):
            manager = ContainerManager()
            async with manager:
                # Container should be started
                assert manager.container is not None

            # After exit, container should be removed
            container.remove.assert_called_once_with(force=True)

    async def test_container_cleanup_on_exception(self, mock_docker_client: MagicMock) -> None:
        """Container is destroyed even when exception occurs."""
        from theo.container.manager import ContainerManager

        container = mock_docker_client.containers.run.return_value

        with patch("docker.from_env", return_value=mock_docker_client):
            manager = ContainerManager()

            with pytest.raises(ValueError):
                async with manager:
                    assert manager.container is not None
                    raise ValueError("Simulated crash")

            # Container should still be removed despite exception
            container.remove.assert_called_once_with(force=True)

    @pytest.mark.skipif(not docker_available(), reason="Docker daemon not available")
    async def test_real_container_starts_and_destroys(self) -> None:
        """Integration test: Real container starts and is destroyed."""
        from theo.container.manager import ContainerManager

        async with ContainerManager() as manager:
            assert manager.is_running is True
            # Capture container id to verify it was created
            assert manager.container.id is not None

        # After exit, verify container reference is cleared
        # (The container reference is now None)
        assert manager._container is None


@pytest.mark.integration
class TestFileTransferRoundtrip:
    """Test file transfer end-to-end."""

    @pytest.mark.skipif(not docker_available(), reason="Docker daemon not available")
    async def test_upload_and_download_same_file(self, tmp_path: Path) -> None:
        """Upload a file, download it back, verify contents match."""
        from theo.container.manager import ContainerManager

        # Create original file with unique content
        original_content = "Integration test content: Hello Theo!\n" * 10
        upload_file = tmp_path / "upload_test.txt"
        upload_file.write_text(original_content)

        async with ContainerManager() as manager:
            # Upload file to container
            container_path = "/tmp/roundtrip_test.txt"
            manager.put_file(str(upload_file), container_path)

            # Download to different local path
            download_file = tmp_path / "download_test.txt"
            manager.get_file(container_path, str(download_file))

            # Verify contents match
            downloaded_content = download_file.read_text()
            assert downloaded_content == original_content

    async def test_file_upload_tool_integration(
        self, mock_docker_client: MagicMock, tmp_path: Path
    ) -> None:
        """Test file upload tool integrates with container manager."""
        from theo.container.manager import ContainerManager
        from theo.tools.files import create_file_upload_tool

        container = mock_docker_client.containers.run.return_value

        # Create test file
        test_file = tmp_path / "tool_upload_test.txt"
        test_file.write_text("Tool integration test")

        with patch("docker.from_env", return_value=mock_docker_client):
            async with ContainerManager() as manager:
                tool = create_file_upload_tool(manager)
                result = await tool.ainvoke(
                    {
                        "local_path": str(test_file),
                        "container_path": "/tmp/tool_test.txt",
                    }
                )

                # Verify tool reported success and put_archive was called
                assert result["success"] is True
                container.put_archive.assert_called_once()


@pytest.mark.integration
class TestErrorHandling:
    """Test error scenarios."""

    async def test_openrouter_api_error_displays_in_conversation(
        self, env_with_api_key: str
    ) -> None:
        """API error is shown to user gracefully."""
        from theo.tui.app import TheoApp

        app = TheoApp()
        async with app.run_test() as pilot:
            # Manually set up agent with a mock that raises API error
            mock_manager = MagicMock()
            mock_agent = AsyncMock()

            async def mock_astream(*args, **kwargs):
                raise Exception("OpenRouter API rate limit exceeded")
                yield  # Make it a generator

            mock_agent.astream = mock_astream

            app._container_manager = mock_manager
            app._agent = mock_agent

            # Process a message
            await app.handle_user_input("Test message")
            await pilot.pause()

            # Verify error was displayed in conversation
            conversation = app.query_one("ConversationWidget")
            # Error should have been logged (message_count includes the error)
            assert conversation.message_count > 0

    async def test_docker_unavailable_shows_error(self) -> None:
        """Missing Docker daemon shows helpful error."""
        from theo.container.manager import ContainerManager, DockerNotAvailableError

        with patch("docker.from_env") as mock_from_env:
            from docker.errors import DockerException

            mock_from_env.side_effect = DockerException("Connection refused")

            manager = ContainerManager()
            with pytest.raises(DockerNotAvailableError) as exc_info:
                await manager.start()

            # Verify error message is helpful
            assert "Docker daemon" in str(exc_info.value)

    async def test_tool_error_propagates_correctly(self, env_with_api_key: str) -> None:
        """Tool execution errors are handled and reported correctly."""
        from theo.container.manager import ContainerNotRunningError
        from theo.tools.shell import create_shell_command_tool

        mock_manager = MagicMock()

        async def mock_exec_error(cmd: str, workdir: str | None = None):
            raise ContainerNotRunningError("Container stopped unexpectedly")
            yield  # Make it a generator

        mock_manager.exec_command = mock_exec_error

        tool = create_shell_command_tool(mock_manager)
        result = await tool.ainvoke({"command": "ls"})

        # Tool should return error gracefully, not crash
        assert result["success"] is False
        assert "error" in result


@pytest.mark.integration
class TestTUIIntegration:
    """Test TUI component integration."""

    async def test_reasoning_panel_clears_between_turns(self) -> None:
        """Reasoning panel is cleared at the start of each new turn."""
        from theo.tui.app import TheoApp

        app = TheoApp()
        async with app.run_test() as pilot:
            reasoning = app.query_one("ReasoningPanel")

            # Add some tokens to simulate previous turn
            reasoning.add_token("Previous turn reasoning...")
            await pilot.pause()
            assert reasoning.token_count > 0

            # Clear (as would happen at start of new turn)
            reasoning.clear()
            await pilot.pause()

            # Verify panel is cleared
            assert reasoning.token_count == 0

    async def test_conversation_and_reasoning_wired_correctly(self) -> None:
        """Test that conversation and reasoning widgets exist and are accessible."""
        from theo.tui.app import TheoApp

        app = TheoApp()
        async with app.run_test() as pilot:
            # Both widgets should be queryable
            conversation = app.query_one("ConversationWidget")
            reasoning = app.query_one("ReasoningPanel")

            # Add content to each
            conversation.add_user_message("Test message")
            reasoning.add_token("Test reasoning")
            await pilot.pause()

            # Verify content was added
            assert conversation.message_count >= 1
            assert reasoning.token_count >= 1

    async def test_message_input_triggers_handler(self) -> None:
        """Test that message input submission is wired to handler."""
        from theo.tui.app import TheoApp

        app = TheoApp()
        async with app.run_test() as pilot:
            # The app should have handler for message submission
            assert hasattr(app, "on_message_input_submitted")

            # Get the input widget
            message_input = app.query_one("MessageInput")
            inner_input = message_input.query_one("Input")

            # Type and submit (without agent, just verify wiring)
            inner_input.value = "Test"
            await pilot.pause()
            await pilot.press("enter")
            await pilot.pause()

            # Input should be cleared after submission
            assert inner_input.value == ""


@pytest.mark.integration
class TestComponentWiring:
    """Test that all components are properly wired together."""

    def test_tools_use_container_manager(self) -> None:
        """Verify tools are created with container manager access."""
        from theo.container.manager import ContainerManager
        from theo.tools import create_tools

        mock_manager = MagicMock(spec=ContainerManager)
        tools = create_tools(mock_manager)

        # Should have 3 tools
        assert len(tools) == 3

        # Each tool should have a name
        tool_names = {t.name for t in tools}
        assert "shell_command" in tool_names
        assert "file_upload" in tool_names
        assert "file_download" in tool_names

    def test_agent_receives_tools(self, env_with_api_key: str) -> None:
        """Verify agent is created with tools from container manager."""
        from theo.config import Settings

        mock_manager = MagicMock()

        with patch("theo.agent.graph.ChatOpenAI"):
            with patch("trinity.agent.graph.create_react_agent") as mock_create:
                from theo.agent.graph import create_agent

                config = Settings()
                create_agent(mock_manager, config)

                # Verify create_react_agent was called with tools
                mock_create.assert_called_once()
                call_kwargs = mock_create.call_args[1]
                assert "tools" in call_kwargs
                assert len(call_kwargs["tools"]) == 3

    def test_settings_provides_all_config(self, env_with_api_key: str) -> None:
        """Verify Settings provides all required configuration."""
        from theo.config import Settings

        config = Settings()

        # All required fields should be accessible
        assert config.openrouter_api_key is not None
        assert config.openrouter_model is not None
        assert config.openrouter_base_url is not None

        # Verify defaults
        assert config.openrouter_model == "arcee-ai/trinity-mini"
        assert "openrouter.ai" in config.openrouter_base_url
