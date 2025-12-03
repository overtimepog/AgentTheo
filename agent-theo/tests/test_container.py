"""Tests for Docker container management.

This module tests the ContainerManager class which handles the lifecycle
of Kali Linux containers for Theo Agent.
"""

import io
import tarfile
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

from theo.container.manager import ContainerManager, DockerNotAvailableError

# --- Fixtures ---


@pytest.fixture
def mock_docker_client() -> MagicMock:
    """Create a mock Docker client."""
    client = MagicMock()
    container = MagicMock()
    container.id = "test-container-id"
    container.status = "running"
    container.name = "theo-test-container"
    client.containers.run.return_value = container
    return client


@pytest.fixture
def mock_container() -> MagicMock:
    """Create a mock container instance."""
    container = MagicMock()
    container.id = "test-container-id"
    container.status = "running"
    container.name = "theo-test-container"
    return container


# --- Unit Tests (Mocked) ---


class TestContainerManagerCreation:
    """Tests for container creation and configuration."""

    async def test_creates_container_with_kali_image(self, mock_docker_client: MagicMock) -> None:
        """Container should be created with kalilinux/kali-rolling image."""
        with patch("docker.from_env", return_value=mock_docker_client):
            manager = ContainerManager()
            await manager.start()

        mock_docker_client.containers.run.assert_called_once()
        call_args = mock_docker_client.containers.run.call_args
        assert call_args[0][0] == "kalilinux/kali-rolling"

    async def test_container_has_correct_configuration(self, mock_docker_client: MagicMock) -> None:
        """Container should be created with detach=True, tty=True, stdin_open=True."""
        with patch("docker.from_env", return_value=mock_docker_client):
            manager = ContainerManager()
            await manager.start()

        call_kwargs = mock_docker_client.containers.run.call_args[1]
        assert call_kwargs.get("detach") is True
        assert call_kwargs.get("tty") is True
        assert call_kwargs.get("stdin_open") is True


class TestContainerManagerCleanup:
    """Tests for container cleanup and removal."""

    async def test_container_removed_on_stop(self, mock_docker_client: MagicMock) -> None:
        """Container should be removed with force=True on stop."""
        container = mock_docker_client.containers.run.return_value

        with patch("docker.from_env", return_value=mock_docker_client):
            manager = ContainerManager()
            await manager.start()
            await manager.stop()

        container.remove.assert_called_once_with(force=True)

    async def test_context_manager_cleanup(self, mock_docker_client: MagicMock) -> None:
        """Container should be cleaned up when using context manager."""
        container = mock_docker_client.containers.run.return_value

        with patch("docker.from_env", return_value=mock_docker_client):
            async with ContainerManager() as manager:
                assert manager.container is not None

        container.remove.assert_called_once_with(force=True)


class TestContainerExecution:
    """Tests for command execution in container."""

    async def test_exec_run_returns_streaming_iterator(self, mock_docker_client: MagicMock) -> None:
        """exec_command should return an async iterator of (stdout, stderr) chunks."""
        container = mock_docker_client.containers.run.return_value

        # Mock exec_run with demux=True returning separate stdout/stderr
        mock_output = iter([(b"hello\n", None), (None, b"error\n"), (b"world\n", None)])
        exec_result = MagicMock()
        exec_result.output = mock_output
        exec_result.exit_code = 0
        container.exec_run.return_value = exec_result

        with patch("docker.from_env", return_value=mock_docker_client):
            manager = ContainerManager()
            await manager.start()

            chunks = []
            async for stdout, stderr in manager.exec_command("echo hello"):
                chunks.append((stdout, stderr))

        # Verify exec_run was called with correct parameters
        container.exec_run.assert_called_once()
        call_kwargs = container.exec_run.call_args[1]
        assert call_kwargs.get("stream") is True
        assert call_kwargs.get("demux") is True


class TestDockerAvailability:
    """Tests for Docker daemon availability handling."""

    async def test_error_when_docker_unavailable(self) -> None:
        """Should raise DockerNotAvailableError when Docker daemon is unavailable."""
        with patch("docker.from_env") as mock_from_env:
            from docker.errors import DockerException

            mock_from_env.side_effect = DockerException("Connection refused")

            with pytest.raises(DockerNotAvailableError) as exc_info:
                manager = ContainerManager()
                await manager.start()

            assert "Docker daemon" in str(exc_info.value)


class TestFileTransfer:
    """Tests for file upload and download functionality."""

    async def test_put_file_uploads_to_container(
        self, mock_docker_client: MagicMock, tmp_path: Path
    ) -> None:
        """put_file should upload local file to container using put_archive."""
        container = mock_docker_client.containers.run.return_value

        # Create a test file
        test_file = tmp_path / "test.txt"
        test_file.write_text("test content")

        with patch("docker.from_env", return_value=mock_docker_client):
            manager = ContainerManager()
            await manager.start()
            manager.put_file(str(test_file), "/tmp/test.txt")

        # Verify put_archive was called
        container.put_archive.assert_called_once()
        call_args = container.put_archive.call_args
        # First arg should be the directory path
        assert call_args[0][0] == "/tmp"

    async def test_get_file_downloads_from_container(
        self, mock_docker_client: MagicMock, tmp_path: Path
    ) -> None:
        """get_file should download file from container using get_archive."""
        container = mock_docker_client.containers.run.return_value

        # Create mock tar archive with test content
        tar_buffer = io.BytesIO()
        with tarfile.open(fileobj=tar_buffer, mode="w") as tar:
            content = b"downloaded content"
            tarinfo = tarfile.TarInfo(name="remote_file.txt")
            tarinfo.size = len(content)
            tar.addfile(tarinfo, io.BytesIO(content))
        tar_buffer.seek(0)

        # Mock get_archive to return our tar buffer
        container.get_archive.return_value = (iter([tar_buffer.getvalue()]), {"size": 100})

        local_dest = tmp_path / "downloaded.txt"

        with patch("docker.from_env", return_value=mock_docker_client):
            manager = ContainerManager()
            await manager.start()
            manager.get_file("/tmp/remote_file.txt", str(local_dest))

        # Verify get_archive was called
        container.get_archive.assert_called_once_with("/tmp/remote_file.txt")


# --- Integration Test (Requires Docker) ---


def docker_available() -> bool:
    """Check if Docker daemon is available."""
    try:
        import docker

        client = docker.from_env()
        client.ping()
        return True
    except Exception:
        return False


@pytest.mark.skipif(not docker_available(), reason="Docker daemon not available")
class TestContainerIntegration:
    """Integration tests that require a real Docker daemon."""

    async def test_real_container_lifecycle(self) -> None:
        """Test real container creation, command execution, and cleanup."""
        async with ContainerManager() as manager:
            # Verify container is running (is_running calls reload)
            assert manager.container is not None
            assert manager.is_running is True

            # Execute a simple command
            output_chunks = []
            async for stdout, stderr in manager.exec_command("echo 'hello from container'"):
                if stdout:
                    output_chunks.append(stdout)

            # Verify we got output
            full_output = "".join(output_chunks)
            assert "hello from container" in full_output

        # After context exit, container should be removed
        # (Cannot easily verify removal without keeping reference)

    async def test_real_file_transfer_roundtrip(self, tmp_path: Path) -> None:
        """Test uploading and downloading a file to/from real container."""
        # Create a test file
        local_file = tmp_path / "upload_test.txt"
        local_file.write_text("roundtrip test content")

        async with ContainerManager() as manager:
            # Upload file
            manager.put_file(str(local_file), "/tmp/upload_test.txt")

            # Download to different location
            download_path = tmp_path / "downloaded_test.txt"
            manager.get_file("/tmp/upload_test.txt", str(download_path))

            # Verify content matches
            assert download_path.read_text() == "roundtrip test content"
