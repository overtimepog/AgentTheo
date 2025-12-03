"""File transfer tools for Theo Agent.

This module provides LangChain-compatible tools for uploading and downloading
files between the local machine and the Kali Linux container.
"""

from pathlib import Path
from typing import TYPE_CHECKING, Any

from langchain_core.tools import tool

if TYPE_CHECKING:
    from theo.container.manager import ContainerManager


def create_file_upload_tool(container_manager: "ContainerManager"):
    """Create a file upload tool bound to a specific container manager.

    This factory function creates a LangChain tool that uploads files from
    the local filesystem to the container.

    Args:
        container_manager: The ContainerManager instance to use for file transfer.

    Returns:
        A LangChain tool function decorated with @tool.

    Example:
        >>> manager = ContainerManager()
        >>> upload_tool = create_file_upload_tool(manager)
        >>> result = await upload_tool.ainvoke({
        ...     "local_path": "/tmp/exploit.py",
        ...     "container_path": "/root/exploit.py"
        ... })
    """

    @tool
    async def file_upload(local_path: str, container_path: str) -> dict[str, Any]:
        """Upload a file from the local machine to the Kali container.

        This tool transfers a file from your local filesystem into the
        isolated Kali Linux container. Use this to provide scripts, wordlists,
        payloads, or any other files the container needs for security testing.

        Args:
            local_path: Absolute path to the file on the local machine
                       (e.g., "/home/user/scripts/scanner.py")
            container_path: Destination path inside the container
                           (e.g., "/root/scanner.py", "/tmp/wordlist.txt")

        Returns:
            A dictionary containing:
            - success: Boolean indicating if the upload succeeded
            - local_path: The source file path
            - container_path: The destination file path in the container
            - error: Error message if the upload failed

        Examples:
            - Upload a Python script: local="/tmp/scan.py", container="/root/scan.py"
            - Upload a wordlist: local="/usr/share/wordlists/rockyou.txt",
                                container="/tmp/rockyou.txt"
        """
        local_file = Path(local_path)

        # Validate local file exists before attempting transfer
        if not local_file.exists():
            return {
                "success": False,
                "local_path": local_path,
                "container_path": container_path,
                "error": f"Local file not found: {local_path}",
            }

        if not local_file.is_file():
            return {
                "success": False,
                "local_path": local_path,
                "container_path": container_path,
                "error": f"Path is not a file: {local_path}",
            }

        try:
            container_manager.put_file(local_path, container_path)
            return {
                "success": True,
                "local_path": local_path,
                "container_path": container_path,
                "error": None,
            }
        except Exception as e:
            return {
                "success": False,
                "local_path": local_path,
                "container_path": container_path,
                "error": str(e),
            }

    return file_upload


def create_file_download_tool(container_manager: "ContainerManager"):
    """Create a file download tool bound to a specific container manager.

    This factory function creates a LangChain tool that downloads files from
    the container to the local filesystem.

    Args:
        container_manager: The ContainerManager instance to use for file transfer.

    Returns:
        A LangChain tool function decorated with @tool.

    Example:
        >>> manager = ContainerManager()
        >>> download_tool = create_file_download_tool(manager)
        >>> result = await download_tool.ainvoke({
        ...     "container_path": "/root/scan_results.txt",
        ...     "local_path": "/tmp/results.txt"
        ... })
    """

    @tool
    async def file_download(container_path: str, local_path: str) -> dict[str, Any]:
        """Download a file from the Kali container to the local machine.

        This tool retrieves a file from inside the isolated Kali Linux
        container and saves it to your local filesystem. Use this to
        save scan results, captured data, logs, or any files generated
        during security testing.

        Args:
            container_path: Path to the file inside the container
                           (e.g., "/root/nmap_scan.xml", "/tmp/results.txt")
            local_path: Destination path on the local machine
                       (e.g., "/home/user/results/scan.xml")

        Returns:
            A dictionary containing:
            - success: Boolean indicating if the download succeeded
            - container_path: The source file path in the container
            - local_path: The destination file path on local machine
            - file_size: Size of the downloaded file in bytes (if successful)
            - error: Error message if the download failed

        Examples:
            - Download scan results: container="/root/nmap.xml", local="/tmp/nmap.xml"
            - Download captured data: container="/tmp/capture.pcap",
                                      local="/home/user/capture.pcap"
        """
        local_file = Path(local_path)

        try:
            # Create parent directory if it doesn't exist
            local_file.parent.mkdir(parents=True, exist_ok=True)

            container_manager.get_file(container_path, local_path)

            # Get file size after download
            file_size = local_file.stat().st_size if local_file.exists() else 0

            return {
                "success": True,
                "container_path": container_path,
                "local_path": local_path,
                "file_size": file_size,
                "error": None,
            }
        except FileNotFoundError:
            return {
                "success": False,
                "container_path": container_path,
                "local_path": local_path,
                "file_size": 0,
                "error": f"File not found in container: {container_path}",
            }
        except Exception as e:
            return {
                "success": False,
                "container_path": container_path,
                "local_path": local_path,
                "file_size": 0,
                "error": str(e),
            }

    return file_download
