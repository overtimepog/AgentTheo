"""Shell command tool for Theo Agent.

This module provides a LangChain-compatible tool for executing shell commands
inside the Kali Linux container with streaming output support.
"""

from typing import TYPE_CHECKING, Any

from langchain_core.tools import tool

if TYPE_CHECKING:
    from theo.container.manager import ContainerManager


def create_shell_command_tool(container_manager: "ContainerManager"):
    """Create a shell command tool bound to a specific container manager.

    This factory function creates a LangChain tool that executes shell commands
    in the container managed by the provided ContainerManager instance.

    Args:
        container_manager: The ContainerManager instance to use for command execution.

    Returns:
        A LangChain tool function decorated with @tool.

    Example:
        >>> manager = ContainerManager()
        >>> shell_tool = create_shell_command_tool(manager)
        >>> result = await shell_tool.ainvoke({"command": "whoami"})
        >>> print(result["stdout"])
        root
    """

    @tool
    async def shell_command(command: str) -> dict[str, Any]:
        """Execute a shell command in the Kali Linux container.

        This tool runs the specified command inside an isolated Kali Linux
        container and returns the output. Use this for any shell operations
        including running security tools, file operations, network commands,
        and system administration tasks.

        Args:
            command: The shell command to execute (e.g., "nmap -sV localhost",
                    "cat /etc/passwd", "ls -la /tmp")

        Returns:
            A dictionary containing:
            - stdout: Standard output from the command
            - stderr: Standard error from the command
            - exit_code: The command's exit code (0 typically means success)
            - success: Boolean indicating if the command executed without errors
            - error: Error message if the command failed to execute

        Examples:
            - "whoami" -> Shows current user
            - "nmap -sV 192.168.1.1" -> Scans host for services
            - "cat /etc/passwd" -> Shows user accounts
            - "ifconfig" -> Shows network interfaces
        """
        stdout_parts: list[str] = []
        stderr_parts: list[str] = []
        exit_code = 0
        error_message: str | None = None

        try:
            async for stdout_chunk, stderr_chunk in container_manager.exec_command(command):
                if stdout_chunk:
                    stdout_parts.append(stdout_chunk)
                if stderr_chunk:
                    stderr_parts.append(stderr_chunk)

            return {
                "stdout": "".join(stdout_parts),
                "stderr": "".join(stderr_parts),
                "exit_code": exit_code,
                "success": True,
                "error": None,
            }

        except Exception as e:
            error_message = str(e)
            return {
                "stdout": "".join(stdout_parts),
                "stderr": "".join(stderr_parts),
                "exit_code": 1,
                "success": False,
                "error": error_message,
            }

    return shell_command
