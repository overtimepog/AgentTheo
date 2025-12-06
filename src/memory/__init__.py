"""
Semantic Memory System

Provides persistent semantic memory capabilities for AgentTheo using
OpenRouter embeddings and Qdrant vector database.

Usage:
    from src.memory import get_memory_manager, MemoryConfig

    # Get the memory manager singleton
    manager = get_memory_manager()

    # Store a memory
    memory_id = manager.store(
        content="Important information to remember",
        memory_type="document",
        metadata={"source": "user"}
    )

    # Search memories
    results = manager.search("information", k=5)

    # Get auto-retrieval context
    context = manager.get_context("What do you know about X?")
"""

from .config import (
    MemoryConfig,
    get_memory_config,
    reset_memory_config,
)
from .embeddings import (
    OpenRouterEmbeddings,
    OpenRouterEmbeddingError,
)
from .manager import (
    MemoryManager,
    MemoryManagerError,
    get_memory_manager,
    MEMORY_TYPES,
)

__all__ = [
    # Config
    "MemoryConfig",
    "get_memory_config",
    "reset_memory_config",
    # Embeddings
    "OpenRouterEmbeddings",
    "OpenRouterEmbeddingError",
    # Manager
    "MemoryManager",
    "MemoryManagerError",
    "get_memory_manager",
    "MEMORY_TYPES",
]
