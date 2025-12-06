"""
Memory Configuration

Configuration management for the semantic memory system.
Loads settings from environment variables with sensible defaults.
"""

import os
from dataclasses import dataclass, field
from pathlib import Path
from typing import Optional


@dataclass
class MemoryConfig:
    """
    Configuration for the semantic memory system.

    All settings can be overridden via environment variables.
    """

    # OpenRouter API settings (reuse existing keys)
    api_key: str = field(default_factory=lambda: os.getenv("THEO_OPENROUTER_API_KEY", ""))
    embedding_model: str = field(
        default_factory=lambda: os.getenv(
            "THEO_OPENROUTER_EMBEDDING_MODEL",
            "openai/text-embedding-3-large"
        )
    )
    base_url: str = "https://openrouter.ai/api/v1"

    # Vector database settings
    vectordb_path: Path = field(default_factory=lambda: Path(
        os.path.expanduser(os.getenv("THEO_VECTORDB_PATH", "~/.theo/vectordb/"))
    ))
    collection_name: str = "theo_memories"

    # Embedding dimensions by model (text-embedding-3-large = 3072)
    vector_dimensions: int = field(default_factory=lambda: int(
        os.getenv("THEO_MEMORY_VECTOR_DIMENSIONS", "3072")
    ))

    # Auto-retrieval settings
    enabled: bool = field(default_factory=lambda: os.getenv(
        "THEO_MEMORY_ENABLED", "true"
    ).lower() in ("true", "1", "yes"))

    auto_retrieve_enabled: bool = field(default_factory=lambda: os.getenv(
        "THEO_MEMORY_AUTO_RETRIEVE_ENABLED", "true"
    ).lower() in ("true", "1", "yes"))

    auto_retrieve_k: int = field(default_factory=lambda: int(
        os.getenv("THEO_MEMORY_AUTO_RETRIEVE_K", "5")
    ))

    # Content limits
    max_content_length: int = field(default_factory=lambda: int(
        os.getenv("THEO_MEMORY_MAX_CONTENT_LENGTH", "8000")
    ))

    # Embedding batch size
    embedding_batch_size: int = field(default_factory=lambda: int(
        os.getenv("THEO_MEMORY_EMBEDDING_BATCH_SIZE", "50")
    ))

    def __post_init__(self):
        """Validate configuration after initialization."""
        if not self.api_key:
            # Don't raise, just warn - memory can be disabled
            pass

        # Ensure vectordb path is a Path object
        if isinstance(self.vectordb_path, str):
            self.vectordb_path = Path(os.path.expanduser(self.vectordb_path))

    def ensure_vectordb_directory(self) -> Path:
        """Create the vector database directory if it doesn't exist."""
        self.vectordb_path.mkdir(parents=True, exist_ok=True)
        return self.vectordb_path

    @classmethod
    def from_env(cls) -> "MemoryConfig":
        """Create a MemoryConfig instance from environment variables."""
        return cls()

    def is_configured(self) -> bool:
        """Check if the memory system is properly configured."""
        return bool(self.api_key) and self.enabled


# Singleton instance
_config_instance: Optional[MemoryConfig] = None


def get_memory_config() -> MemoryConfig:
    """Get the global MemoryConfig instance (singleton)."""
    global _config_instance
    if _config_instance is None:
        _config_instance = MemoryConfig.from_env()
    return _config_instance


def reset_memory_config() -> None:
    """Reset the global config instance. Useful for testing."""
    global _config_instance
    _config_instance = None
