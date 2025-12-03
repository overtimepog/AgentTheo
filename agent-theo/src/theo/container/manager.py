"""Docker container management for Theo Agent.

This module provides the ContainerManager class which handles the complete
lifecycle of Kali Linux containers used for command execution.
"""

import asyncio
import io
import tarfile
from collections.abc import AsyncIterator
from pathlib import Path
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    import docker
    from docker.models.containers import Container


class DockerNotAvailableError(Exception):
    """Raised when Docker daemon is not available."""

    def __init__(self, message: str = "Docker daemon is not available or not running") -> None:
        super().__init__(message)
        self.message = message


class ContainerNotRunningError(Exception):
    """Raised when attempting to execute on a container that is not running."""

    def __init__(self, message: str = "Container is not running") -> None:
        super().__init__(message)
        self.message = message


class ContainerManager:
    """Manages Docker container lifecycle for Theo Agent.

    This class handles creation, execution, file transfer, and cleanup of
    Kali Linux containers. It supports async context manager protocol for
    automatic resource management.

    Attributes:
        container: The Docker container instance, or None if not started.
        image: The Docker image to use (default: kalilinux/kali-rolling).

    Example:
        >>> async with ContainerManager() as manager:
        ...     async for stdout, stderr in manager.exec_command("whoami"):
        ...         if stdout:
        ...             print(stdout, end="")
        root
    """

    DEFAULT_IMAGE = "kalilinux/kali-rolling"

    def __init__(self, image: str | None = None) -> None:
        """Initialize the ContainerManager.

        Args:
            image: Docker image to use. Defaults to kalilinux/kali-rolling.
        """
        self._client: docker.DockerClient | None = None
        self._container: Container | None = None
        self._image = image or self.DEFAULT_IMAGE

    @property
    def container(self) -> "Container | None":
        """The Docker container instance, or None if not started."""
        return self._container

    @property
    def is_running(self) -> bool:
        """Check if the container is currently running."""
        if self._container is None:
            return False
        try:
            self._container.reload()
            return self._container.status == "running"
        except Exception:
            return False

    def _ensure_client(self) -> "docker.DockerClient":
        """Ensure Docker client is initialized and connected.

        Returns:
            The Docker client instance.

        Raises:
            DockerNotAvailableError: If Docker daemon is not available.
        """
        if self._client is not None:
            return self._client

        try:
            import docker
            from docker.errors import DockerException

            self._client = docker.from_env()
            # Test connection
            self._client.ping()
            return self._client
        except DockerException as e:
            raise DockerNotAvailableError(f"Docker daemon is not available: {e}") from e
        except Exception as e:
            raise DockerNotAvailableError(f"Failed to connect to Docker daemon: {e}") from e

    def _ensure_running(self) -> "Container":
        """Ensure the container is running.

        Returns:
            The running container instance.

        Raises:
            ContainerNotRunningError: If container is not running.
        """
        if self._container is None:
            raise ContainerNotRunningError("Container has not been started")

        try:
            self._container.reload()
            if self._container.status != "running":
                raise ContainerNotRunningError(
                    f"Container is in state '{self._container.status}', expected 'running'"
                )
            return self._container
        except ContainerNotRunningError:
            raise
        except Exception as e:
            raise ContainerNotRunningError(f"Failed to check container status: {e}") from e

    async def start(self) -> None:
        """Create and start the Kali container.

        This method creates a new container with the configured image and
        starts it in detached mode with TTY and stdin enabled. It waits for
        the container to reach the 'running' state before returning.

        Raises:
            DockerNotAvailableError: If Docker daemon is not available.
            ContainerNotRunningError: If container fails to start.
        """
        client = self._ensure_client()

        # Run container creation in thread pool to avoid blocking
        loop = asyncio.get_event_loop()
        self._container = await loop.run_in_executor(
            None,
            lambda: client.containers.run(
                self._image,
                detach=True,
                tty=True,
                stdin_open=True,
                # Keep container running with a simple command
                command="/bin/bash",
                # Auto-remove is handled by our stop() method
                remove=False,
            ),
        )

        # Wait for container to be in running state
        await self._wait_for_running()

    async def _wait_for_running(self, timeout: float = 30.0) -> None:
        """Wait for the container to reach 'running' state.

        Args:
            timeout: Maximum time to wait in seconds.

        Raises:
            ContainerNotRunningError: If container fails to start within timeout.
        """
        if self._container is None:
            raise ContainerNotRunningError("Container has not been started")

        start_time = asyncio.get_event_loop().time()
        while True:
            self._container.reload()
            if self._container.status == "running":
                return

            if self._container.status in ("exited", "dead"):
                raise ContainerNotRunningError(
                    f"Container failed to start (status: {self._container.status})"
                )

            elapsed = asyncio.get_event_loop().time() - start_time
            if elapsed > timeout:
                status = self._container.status
                raise ContainerNotRunningError(
                    f"Container failed to start within {timeout}s (status: {status})"
                )

            await asyncio.sleep(0.1)

    async def stop(self) -> None:
        """Remove the container with force=True.

        This method forcefully removes the container, stopping it first if
        it is still running. Safe to call even if container is not running.
        """
        if self._container is None:
            return

        loop = asyncio.get_event_loop()
        try:
            await loop.run_in_executor(
                None,
                lambda: self._container.remove(force=True),
            )
        except Exception:
            # Container may already be removed or in an invalid state
            pass
        finally:
            self._container = None

    async def exec_command(
        self, cmd: str, workdir: str | None = None
    ) -> AsyncIterator[tuple[str | None, str | None]]:
        """Execute a command in the container with streaming output.

        Args:
            cmd: The command to execute.
            workdir: Optional working directory for the command.

        Yields:
            Tuples of (stdout_chunk, stderr_chunk). Each tuple contains the
            chunk of output from stdout and stderr respectively, with None
            for the stream that has no data in that chunk.

        Raises:
            ContainerNotRunningError: If container is not running.

        Example:
            >>> async for stdout, stderr in manager.exec_command("ls -la"):
            ...     if stdout:
            ...         print(stdout, end="")
            ...     if stderr:
            ...         print(stderr, end="", file=sys.stderr)
        """
        container = self._ensure_running()
        loop = asyncio.get_event_loop()

        # Execute command in thread pool
        exec_kwargs = {
            "stream": True,
            "demux": True,
            "tty": False,  # Disable TTY for proper demux
        }
        if workdir:
            exec_kwargs["workdir"] = workdir

        result = await loop.run_in_executor(
            None,
            lambda: container.exec_run(cmd, **exec_kwargs),
        )

        # Stream output chunks
        output_iterator = result.output

        # Process output in thread pool and yield results
        for stdout_chunk, stderr_chunk in output_iterator:
            stdout_str = stdout_chunk.decode("utf-8", errors="replace") if stdout_chunk else None
            stderr_str = stderr_chunk.decode("utf-8", errors="replace") if stderr_chunk else None
            yield stdout_str, stderr_str

    def put_file(self, local_path: str, container_path: str) -> None:
        """Upload a file from local filesystem to the container.

        Creates a tar archive of the local file and uses put_archive to
        transfer it to the container.

        Args:
            local_path: Path to the local file to upload.
            container_path: Destination path in the container.

        Raises:
            ContainerNotRunningError: If container is not running.
            FileNotFoundError: If local file does not exist.
            OSError: If file cannot be read.
        """
        container = self._ensure_running()

        local_file = Path(local_path)
        if not local_file.exists():
            raise FileNotFoundError(f"Local file not found: {local_path}")

        # Determine container directory and filename
        container_file = Path(container_path)
        container_dir = str(container_file.parent)
        filename = container_file.name

        # Create tar archive in memory
        tar_buffer = io.BytesIO()
        with tarfile.open(fileobj=tar_buffer, mode="w") as tar:
            tar.add(str(local_file), arcname=filename)
        tar_buffer.seek(0)

        # Upload to container
        container.put_archive(container_dir, tar_buffer.getvalue())

    def get_file(self, container_path: str, local_path: str) -> None:
        """Download a file from the container to local filesystem.

        Uses get_archive to retrieve the file as a tar archive and extracts
        it to the local destination.

        Args:
            container_path: Path to the file in the container.
            local_path: Destination path on local filesystem.

        Raises:
            ContainerNotRunningError: If container is not running.
            FileNotFoundError: If container file does not exist.
        """
        container = self._ensure_running()

        # Get file from container as tar archive
        bits, stat = container.get_archive(container_path)

        # Collect all chunks into a single bytes object
        tar_data = b"".join(bits)

        # Extract the file
        tar_buffer = io.BytesIO(tar_data)
        with tarfile.open(fileobj=tar_buffer, mode="r") as tar:
            # Get the first (and should be only) member
            members = tar.getmembers()
            if not members:
                raise FileNotFoundError(f"No file found at container path: {container_path}")

            member = members[0]

            # Extract file content
            file_obj = tar.extractfile(member)
            if file_obj is None:
                raise FileNotFoundError(f"Cannot extract file: {container_path}")

            # Ensure local directory exists
            local_file = Path(local_path)
            local_file.parent.mkdir(parents=True, exist_ok=True)

            # Write to local file
            local_file.write_bytes(file_obj.read())

    async def health_check(self) -> bool:
        """Check if the container is healthy and responsive.

        Performs a simple command execution to verify the container is
        functioning properly.

        Returns:
            True if container is healthy, False otherwise.
        """
        if not self.is_running:
            return False

        try:
            # Run a simple command to verify container is responsive
            async for stdout, stderr in self.exec_command("echo health"):
                pass
            return True
        except Exception:
            return False

    async def __aenter__(self) -> "ContainerManager":
        """Async context manager entry.

        Starts the container and returns self.

        Returns:
            The ContainerManager instance with container started.
        """
        await self.start()
        return self

    async def __aexit__(
        self,
        exc_type: type[BaseException] | None,
        exc_val: BaseException | None,
        exc_tb: object,
    ) -> None:
        """Async context manager exit.

        Stops and removes the container, even if an exception occurred.
        """
        await self.stop()
