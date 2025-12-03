"""Tools module for Theo Agent.

This module provides LangChain-compatible tools for the Theo Agent,
including shell command execution and file transfer capabilities.

The tools are designed to work with the ContainerManager to execute
operations inside an isolated Kali Linux container.

Usage:
    >>> from theo.container.manager import ContainerManager
    >>> from theo.tools import create_tools
    >>>
    >>> async with ContainerManager() as manager:
    ...     tools = create_tools(manager)
    ...     # tools is a list of LangChain tools ready for agent use
"""

from typing import TYPE_CHECKING

from theo.tools.files import create_file_download_tool, create_file_upload_tool
from theo.tools.shell import create_shell_command_tool

if TYPE_CHECKING:
    from langchain_core.tools import BaseTool

    from theo.container.manager import ContainerManager

__all__ = [
    "create_tools",
    "create_shell_command_tool",
    "create_file_upload_tool",
    "create_file_download_tool",
]


def create_tools(container_manager: "ContainerManager") -> list["BaseTool"]:
    """Factory function that creates all tools with container manager access.

    This function creates instances of all available tools, binding them to
    the provided ContainerManager instance. The tools use closures to maintain
    access to the container manager for executing operations.

    Args:
        container_manager: The ContainerManager instance that tools will use
                          for container operations.

    Returns:
        A list of LangChain-compatible tools ready to be registered with an agent.
        Currently includes:
        - shell_command: Execute shell commands in the container
        - file_upload: Upload files from local machine to container
        - file_download: Download files from container to local machine

    Example:
        >>> from theo.container.manager import ContainerManager
        >>> from theo.tools import create_tools
        >>>
        >>> manager = ContainerManager()
        >>> tools = create_tools(manager)
        >>> len(tools)
        3
        >>> [t.name for t in tools]
        ['shell_command', 'file_upload', 'file_download']
    """
    return [
        create_shell_command_tool(container_manager),
        create_file_upload_tool(container_manager),
        create_file_download_tool(container_manager),
    ]
