"""Base tool interface and common types for Theo Agent tools.

This module provides the foundational abstractions for tool implementations,
including result types and error handling patterns.
"""

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from enum import Enum
from typing import Any


class ToolStatus(Enum):
    """Enumeration of possible tool execution statuses."""

    SUCCESS = "success"
    ERROR = "error"
    TIMEOUT = "timeout"
    CANCELLED = "cancelled"


@dataclass
class ToolResult:
    """Result from a tool execution.

    Attributes:
        status: The execution status (success, error, timeout, cancelled).
        output: The primary output from the tool execution.
        error: Error message if status is not SUCCESS.
        metadata: Additional key-value metadata from the execution.

    Example:
        >>> result = ToolResult(
        ...     status=ToolStatus.SUCCESS,
        ...     output="Command executed successfully",
        ...     metadata={"exit_code": 0}
        ... )
        >>> result.is_success
        True
    """

    status: ToolStatus
    output: str = ""
    error: str | None = None
    metadata: dict[str, Any] = field(default_factory=dict)

    @property
    def is_success(self) -> bool:
        """Check if the tool execution was successful."""
        return self.status == ToolStatus.SUCCESS

    def to_dict(self) -> dict[str, Any]:
        """Convert the result to a dictionary for serialization."""
        return {
            "status": self.status.value,
            "output": self.output,
            "error": self.error,
            "metadata": self.metadata,
        }


@dataclass
class ShellResult(ToolResult):
    """Result from a shell command execution.

    Extends ToolResult with shell-specific fields.

    Attributes:
        stdout: Standard output from the command.
        stderr: Standard error from the command.
        exit_code: The command's exit code.
    """

    stdout: str = ""
    stderr: str = ""
    exit_code: int = 0

    def to_dict(self) -> dict[str, Any]:
        """Convert the result to a dictionary for serialization."""
        base = super().to_dict()
        base.update(
            {
                "stdout": self.stdout,
                "stderr": self.stderr,
                "exit_code": self.exit_code,
            }
        )
        return base


@dataclass
class FileTransferResult(ToolResult):
    """Result from a file transfer operation.

    Attributes:
        source_path: The source file path.
        dest_path: The destination file path.
        bytes_transferred: Number of bytes transferred.
    """

    source_path: str = ""
    dest_path: str = ""
    bytes_transferred: int = 0

    def to_dict(self) -> dict[str, Any]:
        """Convert the result to a dictionary for serialization."""
        base = super().to_dict()
        base.update(
            {
                "source_path": self.source_path,
                "dest_path": self.dest_path,
                "bytes_transferred": self.bytes_transferred,
            }
        )
        return base


class ToolError(Exception):
    """Base exception for tool errors.

    Attributes:
        message: Human-readable error message.
        tool_name: Name of the tool that raised the error.
        details: Additional error details.
    """

    def __init__(
        self,
        message: str,
        tool_name: str | None = None,
        details: dict[str, Any] | None = None,
    ) -> None:
        super().__init__(message)
        self.message = message
        self.tool_name = tool_name
        self.details = details or {}

    def to_result(self) -> ToolResult:
        """Convert the error to a ToolResult with ERROR status."""
        return ToolResult(
            status=ToolStatus.ERROR,
            error=self.message,
            metadata={"tool_name": self.tool_name, **self.details},
        )


class ContainerNotRunningError(ToolError):
    """Raised when a tool requires a container but none is running."""

    def __init__(self, tool_name: str | None = None) -> None:
        super().__init__(
            message="Container is not running. Ensure the container is started before executing.",
            tool_name=tool_name,
        )


class CommandTimeoutError(ToolError):
    """Raised when a command execution times out."""

    def __init__(
        self,
        command: str,
        timeout_seconds: float,
        tool_name: str | None = None,
    ) -> None:
        super().__init__(
            message=f"Command timed out after {timeout_seconds}s: {command}",
            tool_name=tool_name,
            details={"command": command, "timeout_seconds": timeout_seconds},
        )


class FileTransferError(ToolError):
    """Raised when a file transfer operation fails."""

    def __init__(
        self,
        message: str,
        source_path: str,
        dest_path: str,
        tool_name: str | None = None,
    ) -> None:
        super().__init__(
            message=message,
            tool_name=tool_name,
            details={"source_path": source_path, "dest_path": dest_path},
        )


class BaseTool(ABC):
    """Abstract base class for Theo Agent tools.

    This provides a common interface for all tools that can be registered
    with the agent. Implementations should override the execute method.

    Attributes:
        name: Unique identifier for the tool.
        description: Human-readable description for LLM context.
    """

    name: str
    description: str

    @abstractmethod
    async def execute(self, **kwargs: Any) -> ToolResult:
        """Execute the tool with the given arguments.

        Args:
            **kwargs: Tool-specific arguments.

        Returns:
            ToolResult: The result of the tool execution.

        Raises:
            ToolError: If the tool execution fails.
        """
        raise NotImplementedError
