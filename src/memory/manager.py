"""
Memory Manager

Core memory management for the semantic memory system.
Handles storage, retrieval, and deletion of memories using Qdrant.
"""

import json
import logging
import uuid
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional, Union

from qdrant_client import QdrantClient
from qdrant_client.http import models
from qdrant_client.http.models import (
    Distance,
    FieldCondition,
    Filter,
    MatchValue,
    PointStruct,
    VectorParams,
)

from .config import get_memory_config, MemoryConfig
from .embeddings import OpenRouterEmbeddings, OpenRouterEmbeddingError

logger = logging.getLogger(__name__)


# Valid memory types
MEMORY_TYPES = {"conversation", "document", "tool_output", "general"}


class MemoryManagerError(Exception):
    """Exception raised for memory manager errors."""
    pass


class MemoryManager:
    """
    Manages semantic memory storage and retrieval using Qdrant.

    This is a singleton class that provides CRUD operations for memories,
    including semantic search and auto-context retrieval.

    Attributes:
        config: MemoryConfig instance
        embeddings: OpenRouterEmbeddings instance
        client: QdrantClient instance
    """

    _instance: Optional["MemoryManager"] = None
    _initialized: bool = False

    def __new__(cls, config: Optional[MemoryConfig] = None) -> "MemoryManager":
        """Singleton pattern implementation."""
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance

    def __init__(self, config: Optional[MemoryConfig] = None):
        """
        Initialize the MemoryManager.

        Args:
            config: Optional MemoryConfig instance
        """
        # Avoid re-initialization
        if self._initialized:
            return

        self.config = config or get_memory_config()
        self._embeddings: Optional[OpenRouterEmbeddings] = None
        self._client: Optional[QdrantClient] = None
        self._initialized = True
        self._collection_ready = False

    @property
    def embeddings(self) -> OpenRouterEmbeddings:
        """Get or create the embeddings instance."""
        if self._embeddings is None:
            self._embeddings = OpenRouterEmbeddings(config=self.config)
        return self._embeddings

    @property
    def client(self) -> QdrantClient:
        """Get or create the Qdrant client."""
        if self._client is None:
            # Ensure directory exists
            db_path = self.config.ensure_vectordb_directory()
            self._client = QdrantClient(path=str(db_path))
            logger.info(f"Initialized Qdrant client at {db_path}")
        return self._client

    def initialize(self) -> None:
        """
        Initialize the Qdrant collection if it doesn't exist.

        Creates the collection with proper vector configuration.
        """
        if self._collection_ready:
            return

        try:
            collections = self.client.get_collections().collections
            collection_names = [c.name for c in collections]

            if self.config.collection_name not in collection_names:
                self.client.create_collection(
                    collection_name=self.config.collection_name,
                    vectors_config=VectorParams(
                        size=self.config.vector_dimensions,
                        distance=Distance.COSINE,
                    ),
                )
                logger.info(f"Created collection: {self.config.collection_name}")
            else:
                logger.debug(f"Collection already exists: {self.config.collection_name}")

            self._collection_ready = True

        except Exception as e:
            logger.error(f"Failed to initialize collection: {e}")
            raise MemoryManagerError(f"Collection initialization failed: {e}") from e

    def _validate_memory_type(self, memory_type: str) -> str:
        """Validate and normalize memory type."""
        memory_type = memory_type.lower().strip()
        if memory_type and memory_type not in MEMORY_TYPES:
            logger.warning(f"Unknown memory type '{memory_type}', using 'general'")
            return "general"
        return memory_type or "general"

    def _generate_memory_id(self) -> str:
        """Generate a unique memory ID."""
        return str(uuid.uuid4())

    def _truncate_content(self, content: str) -> str:
        """Truncate content to max length."""
        max_len = self.config.max_content_length
        if len(content) > max_len:
            return content[:max_len] + "..."
        return content

    def store(
        self,
        content: str,
        memory_type: str = "general",
        metadata: Optional[Dict[str, Any]] = None,
        session_id: Optional[str] = None,
        source: str = "user",
    ) -> str:
        """
        Store a new memory.

        Args:
            content: The text content to store
            memory_type: Type of memory (conversation, document, tool_output, general)
            metadata: Additional custom metadata
            session_id: Optional session/thread ID
            source: Source of the memory (user, tool, system)

        Returns:
            The generated memory ID

        Raises:
            MemoryManagerError: If storage fails
        """
        self.initialize()

        memory_id = self._generate_memory_id()
        memory_type = self._validate_memory_type(memory_type)
        content = self._truncate_content(content)

        try:
            # Generate embedding
            embedding = self.embeddings.embed_query(content)

            # Prepare payload
            payload = {
                "memory_id": memory_id,
                "memory_type": memory_type,
                "content": content,
                "timestamp": datetime.now(timezone.utc).isoformat(),
                "session_id": session_id or "",
                "source": source,
                "custom": metadata or {},
            }

            # Store in Qdrant
            self.client.upsert(
                collection_name=self.config.collection_name,
                points=[
                    PointStruct(
                        id=memory_id,
                        vector=embedding,
                        payload=payload,
                    )
                ],
            )

            logger.info(f"Stored memory {memory_id} (type: {memory_type})")
            return memory_id

        except OpenRouterEmbeddingError as e:
            raise MemoryManagerError(f"Failed to generate embedding: {e}") from e
        except Exception as e:
            raise MemoryManagerError(f"Failed to store memory: {e}") from e

    def search(
        self,
        query: str,
        memory_type: Optional[str] = None,
        k: int = 5,
        score_threshold: Optional[float] = None,
        session_id: Optional[str] = None,
    ) -> List[Dict[str, Any]]:
        """
        Search for relevant memories.

        Args:
            query: Search query text
            memory_type: Optional filter by memory type
            k: Number of results to return
            score_threshold: Minimum similarity score (0-1)
            session_id: Optional filter by session ID

        Returns:
            List of matching memories with scores
        """
        self.initialize()

        try:
            # Generate query embedding
            query_embedding = self.embeddings.embed_query(query)

            # Build filter conditions
            filter_conditions = []

            if memory_type:
                memory_type = self._validate_memory_type(memory_type)
                filter_conditions.append(
                    FieldCondition(
                        key="memory_type",
                        match=MatchValue(value=memory_type),
                    )
                )

            if session_id:
                filter_conditions.append(
                    FieldCondition(
                        key="session_id",
                        match=MatchValue(value=session_id),
                    )
                )

            query_filter = Filter(must=filter_conditions) if filter_conditions else None

            # Search using query_points (newer Qdrant API)
            search_result = self.client.query_points(
                collection_name=self.config.collection_name,
                query=query_embedding,
                query_filter=query_filter,
                limit=k,
                score_threshold=score_threshold,
            )

            # Format results
            memories = []
            for result in search_result.points:
                memory = {
                    "memory_id": result.payload.get("memory_id"),
                    "content": result.payload.get("content"),
                    "memory_type": result.payload.get("memory_type"),
                    "timestamp": result.payload.get("timestamp"),
                    "session_id": result.payload.get("session_id"),
                    "source": result.payload.get("source"),
                    "score": result.score,
                    "custom": result.payload.get("custom", {}),
                }
                memories.append(memory)

            return memories

        except OpenRouterEmbeddingError as e:
            logger.warning(f"Search failed due to embedding error: {e}")
            return []
        except Exception as e:
            logger.error(f"Search failed: {e}")
            return []

    def delete(self, identifier: str) -> bool:
        """
        Delete a memory by ID or by searching for matching content.

        Args:
            identifier: Memory ID (UUID format) or search query

        Returns:
            True if deletion was successful
        """
        self.initialize()

        try:
            # Check if identifier looks like a UUID
            try:
                uuid.UUID(identifier)
                is_uuid = True
            except ValueError:
                is_uuid = False

            if is_uuid:
                # Delete by ID
                self.client.delete(
                    collection_name=self.config.collection_name,
                    points_selector=models.PointIdsList(
                        points=[identifier],
                    ),
                )
                logger.info(f"Deleted memory by ID: {identifier}")
                return True
            else:
                # Search and delete matching memories
                results = self.search(identifier, k=1)
                if results:
                    memory_id = results[0]["memory_id"]
                    self.client.delete(
                        collection_name=self.config.collection_name,
                        points_selector=models.PointIdsList(
                            points=[memory_id],
                        ),
                    )
                    logger.info(f"Deleted memory by query match: {memory_id}")
                    return True
                else:
                    logger.warning(f"No matching memory found for: {identifier}")
                    return False

        except Exception as e:
            logger.error(f"Delete failed: {e}")
            return False

    def delete_by_filter(
        self,
        memory_type: Optional[str] = None,
        session_id: Optional[str] = None,
    ) -> int:
        """
        Delete memories matching filter criteria.

        Args:
            memory_type: Delete all memories of this type
            session_id: Delete all memories from this session

        Returns:
            Number of deleted memories (approximate)
        """
        self.initialize()

        filter_conditions = []

        if memory_type:
            filter_conditions.append(
                FieldCondition(
                    key="memory_type",
                    match=MatchValue(value=self._validate_memory_type(memory_type)),
                )
            )

        if session_id:
            filter_conditions.append(
                FieldCondition(
                    key="session_id",
                    match=MatchValue(value=session_id),
                )
            )

        if not filter_conditions:
            logger.warning("No filter criteria provided for bulk delete")
            return 0

        try:
            self.client.delete(
                collection_name=self.config.collection_name,
                points_selector=models.FilterSelector(
                    filter=Filter(must=filter_conditions),
                ),
            )
            logger.info(f"Bulk deleted memories with filter: {filter_conditions}")
            return -1  # Qdrant doesn't return count

        except Exception as e:
            logger.error(f"Bulk delete failed: {e}")
            return 0

    def list_memories(
        self,
        memory_type: Optional[str] = None,
        limit: int = 10,
        offset: int = 0,
    ) -> List[Dict[str, Any]]:
        """
        List memories, optionally filtered by type.

        Args:
            memory_type: Optional filter by memory type
            limit: Maximum number of results
            offset: Pagination offset

        Returns:
            List of memories with metadata
        """
        self.initialize()

        try:
            filter_conditions = []

            if memory_type:
                filter_conditions.append(
                    FieldCondition(
                        key="memory_type",
                        match=MatchValue(value=self._validate_memory_type(memory_type)),
                    )
                )

            query_filter = Filter(must=filter_conditions) if filter_conditions else None

            # Scroll through collection
            results, _ = self.client.scroll(
                collection_name=self.config.collection_name,
                scroll_filter=query_filter,
                limit=limit,
                offset=offset,
                with_payload=True,
                with_vectors=False,
            )

            memories = []
            for point in results:
                memory = {
                    "memory_id": point.payload.get("memory_id"),
                    "content": point.payload.get("content"),
                    "memory_type": point.payload.get("memory_type"),
                    "timestamp": point.payload.get("timestamp"),
                    "session_id": point.payload.get("session_id"),
                    "source": point.payload.get("source"),
                    "custom": point.payload.get("custom", {}),
                }
                memories.append(memory)

            return memories

        except Exception as e:
            logger.error(f"List memories failed: {e}")
            return []

    def get_context(self, query: str, k: Optional[int] = None) -> str:
        """
        Get formatted context for auto-retrieval.

        This method is used to inject relevant memories into the
        conversation context before the agent responds.

        Args:
            query: The user's query to find relevant context for
            k: Number of memories to retrieve (defaults to config)

        Returns:
            Formatted string of relevant memories, or empty string
        """
        if not self.config.auto_retrieve_enabled:
            return ""

        k = k or self.config.auto_retrieve_k

        try:
            memories = self.search(query, k=k, score_threshold=0.5)

            if not memories:
                return ""

            # Format memories for context injection
            context_parts = ["[Relevant memories from your knowledge base:]"]

            for i, memory in enumerate(memories, 1):
                content = memory["content"]
                mem_type = memory["memory_type"]
                timestamp = memory["timestamp"][:10] if memory["timestamp"] else "unknown"

                context_parts.append(
                    f"\n{i}. [{mem_type}] ({timestamp}): {content}"
                )

            context_parts.append("\n[End of memories]")

            return "\n".join(context_parts)

        except Exception as e:
            logger.warning(f"Failed to get context: {e}")
            return ""

    def get_stats(self) -> Dict[str, Any]:
        """Get memory system statistics."""
        self.initialize()

        try:
            collection_info = self.client.get_collection(self.config.collection_name)
            return {
                "total_memories": collection_info.points_count,
                "collection_name": self.config.collection_name,
                "vector_dimensions": self.config.vector_dimensions,
                "vectordb_path": str(self.config.vectordb_path),
            }
        except Exception as e:
            logger.error(f"Failed to get stats: {e}")
            return {}

    def close(self) -> None:
        """Clean up resources."""
        if self._embeddings is not None:
            self._embeddings.close()
            self._embeddings = None

        if self._client is not None:
            self._client.close()
            self._client = None

        self._collection_ready = False

    @classmethod
    def get_instance(cls, config: Optional[MemoryConfig] = None) -> "MemoryManager":
        """Get the singleton instance."""
        return cls(config)

    @classmethod
    def reset_instance(cls) -> None:
        """Reset the singleton instance. Useful for testing."""
        if cls._instance is not None:
            cls._instance.close()
            cls._instance = None
            cls._initialized = False


# Convenience function
def get_memory_manager() -> MemoryManager:
    """Get the global MemoryManager instance."""
    return MemoryManager.get_instance()
