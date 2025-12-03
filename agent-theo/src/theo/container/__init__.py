"""Container module for Docker management.

This module provides container lifecycle management for Theo Agent,
including creation, execution, file transfer, and cleanup of Kali Linux containers.
"""

from theo.container.manager import (
    ContainerManager,
    ContainerNotRunningError,
    DockerNotAvailableError,
)

__all__ = [
    "ContainerManager",
    "ContainerNotRunningError",
    "DockerNotAvailableError",
]
