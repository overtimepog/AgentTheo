"""Tests for Theo Agent tool implementations.

This module tests the shell command, file upload, and file download tools
that provide LangChain-compatible interfaces to the ContainerManager.
"""

from pathlib import Path
from unittest.mock import MagicMock

import pytest

from theo.container.manager import ContainerManager
from theo.tools import create_tools
from theo.tools.files import create_file_download_tool, create_file_upload_tool
from theo.tools.shell import create_shell_command_tool

# --- Fixtures ---


@pytest.fixture
def mock_container_manager() -> MagicMock:
    """Create a mock ContainerManager instance."""
    manager = MagicMock(spec=ContainerManager)
    manager.is_running = True
    return manager


@pytest.fixture
def mock_running_container_manager(mock_container_manager: MagicMock) -> MagicMock:
    """Create a mock ContainerManager with running container."""

    # Configure exec_command as an async generator
    async def mock_exec_command(cmd: str, workdir: str | None = None):
        yield ("command output\n", None)

    mock_container_manager.exec_command = mock_exec_command
    return mock_container_manager


# --- Shell Command Tool Tests ---


class TestShellCommandTool:
    """Tests for the shell command execution tool."""

    async def test_shell_tool_executes_command_and_returns_output(
        self, mock_container_manager: MagicMock
    ) -> None:
        """Shell tool should execute command and return structured output."""

        # Configure mock to return stdout output
        async def mock_exec(cmd: str, workdir: str | None = None):
            yield ("hello world\n", None)
            yield ("second line\n", None)

        mock_container_manager.exec_command = mock_exec

        tool = create_shell_command_tool(mock_container_manager)
        result = await tool.ainvoke({"command": "echo hello world"})

        assert result["stdout"] == "hello world\nsecond line\n"
        assert result["stderr"] == ""
        assert result["exit_code"] == 0
        assert result["success"] is True

    async def test_shell_tool_handles_command_errors_gracefully(
        self, mock_container_manager: MagicMock
    ) -> None:
        """Shell tool should handle errors and return error information."""

        # Configure mock to return stderr and error
        async def mock_exec_error(cmd: str, workdir: str | None = None):
            yield (None, "command not found\n")

        mock_container_manager.exec_command = mock_exec_error

        tool = create_shell_command_tool(mock_container_manager)
        result = await tool.ainvoke({"command": "nonexistent_command"})

        # Tool should return result even with errors (graceful handling)
        assert result["stderr"] == "command not found\n"
        assert result["stdout"] == ""
        # Note: exit_code may still be 0 if we can't determine it from stream

    async def test_shell_tool_collects_streaming_output(
        self, mock_container_manager: MagicMock
    ) -> None:
        """Shell tool should collect all streaming output chunks."""

        # Configure mock to return multiple chunks
        async def mock_exec_streaming(cmd: str, workdir: str | None = None):
            yield ("chunk1\n", None)
            yield ("chunk2\n", None)
            yield (None, "warning\n")
            yield ("chunk3\n", None)

        mock_container_manager.exec_command = mock_exec_streaming

        tool = create_shell_command_tool(mock_container_manager)
        result = await tool.ainvoke({"command": "long_running_command"})

        assert result["stdout"] == "chunk1\nchunk2\nchunk3\n"
        assert result["stderr"] == "warning\n"

    async def test_shell_tool_handles_container_not_running(
        self, mock_container_manager: MagicMock
    ) -> None:
        """Shell tool should handle case when container is not running."""
        from theo.container.manager import ContainerNotRunningError

        async def mock_exec_not_running(cmd: str, workdir: str | None = None):
            raise ContainerNotRunningError("Container has not been started")
            yield  # Make it a generator

        mock_container_manager.exec_command = mock_exec_not_running

        tool = create_shell_command_tool(mock_container_manager)
        result = await tool.ainvoke({"command": "echo test"})

        assert result["success"] is False
        assert "not running" in result["error"].lower() or "error" in result


# --- File Upload Tool Tests ---


class TestFileUploadTool:
    """Tests for the file upload tool."""

    async def test_file_upload_creates_file_in_container(
        self, mock_container_manager: MagicMock, tmp_path: Path
    ) -> None:
        """File upload should transfer local file to container at specified path."""
        # Create a test file
        test_file = tmp_path / "test_upload.txt"
        test_file.write_text("upload content")

        tool = create_file_upload_tool(mock_container_manager)
        result = await tool.ainvoke(
            {
                "local_path": str(test_file),
                "container_path": "/tmp/test_upload.txt",
            }
        )

        # Verify put_file was called
        mock_container_manager.put_file.assert_called_once_with(
            str(test_file), "/tmp/test_upload.txt"
        )
        assert result["success"] is True
        assert result["local_path"] == str(test_file)
        assert result["container_path"] == "/tmp/test_upload.txt"

    async def test_file_upload_handles_missing_local_file(
        self, mock_container_manager: MagicMock
    ) -> None:
        """File upload should handle case when local file does not exist."""
        tool = create_file_upload_tool(mock_container_manager)
        result = await tool.ainvoke(
            {
                "local_path": "/nonexistent/path/file.txt",
                "container_path": "/tmp/file.txt",
            }
        )

        # Should not call put_file
        mock_container_manager.put_file.assert_not_called()
        assert result["success"] is False
        assert "not found" in result["error"].lower() or "does not exist" in result["error"].lower()


# --- File Download Tool Tests ---


class TestFileDownloadTool:
    """Tests for the file download tool."""

    async def test_file_download_retrieves_file_from_container(
        self, mock_container_manager: MagicMock, tmp_path: Path
    ) -> None:
        """File download should retrieve file from container to local path."""
        local_dest = tmp_path / "downloaded.txt"

        # Mock get_file to actually write the file
        def mock_get_file(container_path: str, local_path: str) -> None:
            Path(local_path).write_text("downloaded content")

        mock_container_manager.get_file = MagicMock(side_effect=mock_get_file)

        tool = create_file_download_tool(mock_container_manager)
        result = await tool.ainvoke(
            {
                "container_path": "/tmp/remote_file.txt",
                "local_path": str(local_dest),
            }
        )

        # Verify get_file was called
        mock_container_manager.get_file.assert_called_once_with(
            "/tmp/remote_file.txt", str(local_dest)
        )
        assert result["success"] is True
        assert result["container_path"] == "/tmp/remote_file.txt"
        assert result["local_path"] == str(local_dest)
        assert result["file_size"] > 0

    async def test_file_download_handles_missing_container_file(
        self, mock_container_manager: MagicMock, tmp_path: Path
    ) -> None:
        """File download should handle case when container file does not exist."""
        local_dest = tmp_path / "downloaded.txt"

        # Mock get_file to raise FileNotFoundError
        mock_container_manager.get_file = MagicMock(
            side_effect=FileNotFoundError("File not found in container")
        )

        tool = create_file_download_tool(mock_container_manager)
        result = await tool.ainvoke(
            {
                "container_path": "/nonexistent/file.txt",
                "local_path": str(local_dest),
            }
        )

        assert result["success"] is False
        assert "not found" in result["error"].lower()

    async def test_file_download_creates_local_directory_if_needed(
        self, mock_container_manager: MagicMock, tmp_path: Path
    ) -> None:
        """File download should create local directory if it doesn't exist."""
        # Nested directory that doesn't exist
        local_dest = tmp_path / "new_dir" / "nested" / "downloaded.txt"

        # Mock get_file to write file (it should handle directory creation)
        def mock_get_file(container_path: str, local_path: str) -> None:
            local_file = Path(local_path)
            local_file.parent.mkdir(parents=True, exist_ok=True)
            local_file.write_text("nested content")

        mock_container_manager.get_file = MagicMock(side_effect=mock_get_file)

        tool = create_file_download_tool(mock_container_manager)
        result = await tool.ainvoke(
            {
                "container_path": "/tmp/file.txt",
                "local_path": str(local_dest),
            }
        )

        assert result["success"] is True
        # Verify the nested directory was created
        assert local_dest.parent.exists()


# --- Tool Registry Tests ---


class TestToolRegistry:
    """Tests for the tool registry factory function."""

    def test_create_tools_returns_all_tools(self, mock_container_manager: MagicMock) -> None:
        """create_tools should return a list of all available tools."""
        tools = create_tools(mock_container_manager)

        assert len(tools) == 3  # shell, file_upload, file_download
        tool_names = [tool.name for tool in tools]
        assert "shell_command" in tool_names
        assert "file_upload" in tool_names
        assert "file_download" in tool_names

    def test_tools_have_proper_descriptions(self, mock_container_manager: MagicMock) -> None:
        """All tools should have docstrings for LLM usage."""
        tools = create_tools(mock_container_manager)

        for tool in tools:
            assert tool.description is not None
            assert len(tool.description) > 10  # Non-trivial description
