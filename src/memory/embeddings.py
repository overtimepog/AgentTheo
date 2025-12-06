"""
OpenRouter Embeddings

Custom LangChain Embeddings implementation that uses OpenRouter's API
for generating text embeddings. Supports batching, retries, and error handling.
"""

import logging
import time
from typing import List, Optional

import httpx
from langchain_core.embeddings import Embeddings
from pydantic import SecretStr

from .config import get_memory_config, MemoryConfig

logger = logging.getLogger(__name__)


class OpenRouterEmbeddingError(Exception):
    """Exception raised when embedding generation fails."""
    pass


class OpenRouterEmbeddings(Embeddings):
    """
    LangChain Embeddings implementation using OpenRouter API.

    Uses the OpenAI-compatible embeddings endpoint at OpenRouter
    to generate vector embeddings for text.

    Attributes:
        api_key: OpenRouter API key
        model: Embedding model name (e.g., "openai/text-embedding-3-large")
        base_url: OpenRouter API base URL
        batch_size: Maximum texts per API call
        max_retries: Maximum number of retry attempts
        timeout: Request timeout in seconds
    """

    def __init__(
        self,
        api_key: Optional[str] = None,
        model: Optional[str] = None,
        base_url: Optional[str] = None,
        batch_size: int = 50,
        max_retries: int = 3,
        timeout: float = 60.0,
        config: Optional[MemoryConfig] = None,
    ):
        """
        Initialize OpenRouterEmbeddings.

        Args:
            api_key: OpenRouter API key (defaults to env var)
            model: Embedding model name (defaults to env var)
            base_url: API base URL (defaults to OpenRouter)
            batch_size: Max texts per API call
            max_retries: Max retry attempts for failed requests
            timeout: Request timeout in seconds
            config: Optional MemoryConfig instance
        """
        self._config = config or get_memory_config()

        self.api_key = SecretStr(api_key or self._config.api_key)
        self.model = model or self._config.embedding_model
        self.base_url = base_url or self._config.base_url
        self.batch_size = batch_size or self._config.embedding_batch_size
        self.max_retries = max_retries
        self.timeout = timeout

        # HTTP client
        self._client: Optional[httpx.Client] = None

    @property
    def client(self) -> httpx.Client:
        """Get or create the HTTP client."""
        if self._client is None or self._client.is_closed:
            self._client = httpx.Client(
                base_url=self.base_url,
                headers={
                    "Authorization": f"Bearer {self.api_key.get_secret_value()}",
                    "Content-Type": "application/json",
                    "HTTP-Referer": "http://localhost",
                },
                timeout=self.timeout,
            )
        return self._client

    def _embed_with_retry(self, texts: List[str]) -> List[List[float]]:
        """
        Generate embeddings with retry logic.

        Args:
            texts: List of texts to embed

        Returns:
            List of embedding vectors

        Raises:
            OpenRouterEmbeddingError: If all retries fail
        """
        last_error: Optional[Exception] = None

        for attempt in range(self.max_retries):
            try:
                response = self.client.post(
                    "/embeddings",
                    json={
                        "model": self.model,
                        "input": texts,
                    },
                )
                response.raise_for_status()

                data = response.json()

                # Extract embeddings from response (OpenAI-compatible format)
                embeddings = []
                for item in sorted(data.get("data", []), key=lambda x: x.get("index", 0)):
                    embeddings.append(item["embedding"])

                return embeddings

            except httpx.HTTPStatusError as e:
                last_error = e
                logger.warning(
                    f"Embedding request failed (attempt {attempt + 1}/{self.max_retries}): "
                    f"HTTP {e.response.status_code}"
                )

                # Don't retry on client errors (except rate limiting)
                if e.response.status_code == 429:
                    # Rate limited - wait longer
                    wait_time = min(2 ** attempt * 2, 30)
                    logger.info(f"Rate limited, waiting {wait_time}s...")
                    time.sleep(wait_time)
                elif 400 <= e.response.status_code < 500:
                    raise OpenRouterEmbeddingError(
                        f"Client error: {e.response.status_code} - {e.response.text}"
                    ) from e
                else:
                    # Server error - retry with backoff
                    time.sleep(2 ** attempt)

            except httpx.RequestError as e:
                last_error = e
                logger.warning(
                    f"Embedding request error (attempt {attempt + 1}/{self.max_retries}): {e}"
                )
                time.sleep(2 ** attempt)

            except Exception as e:
                last_error = e
                logger.error(f"Unexpected error during embedding: {e}")
                raise OpenRouterEmbeddingError(f"Embedding failed: {e}") from e

        raise OpenRouterEmbeddingError(
            f"Failed to generate embeddings after {self.max_retries} attempts: {last_error}"
        )

    def _batch_texts(self, texts: List[str]) -> List[List[str]]:
        """Split texts into batches for efficient API calls."""
        return [
            texts[i:i + self.batch_size]
            for i in range(0, len(texts), self.batch_size)
        ]

    def embed_documents(self, texts: List[str]) -> List[List[float]]:
        """
        Generate embeddings for a list of documents.

        Args:
            texts: List of document texts to embed

        Returns:
            List of embedding vectors (one per document)
        """
        if not texts:
            return []

        # Truncate texts that are too long
        max_len = self._config.max_content_length
        truncated_texts = [
            text[:max_len] if len(text) > max_len else text
            for text in texts
        ]

        all_embeddings = []
        for batch in self._batch_texts(truncated_texts):
            batch_embeddings = self._embed_with_retry(batch)
            all_embeddings.extend(batch_embeddings)

        return all_embeddings

    def embed_query(self, text: str) -> List[float]:
        """
        Generate embedding for a single query text.

        Args:
            text: Query text to embed

        Returns:
            Embedding vector
        """
        # Truncate if too long
        max_len = self._config.max_content_length
        if len(text) > max_len:
            text = text[:max_len]

        embeddings = self._embed_with_retry([text])
        return embeddings[0]

    async def aembed_documents(self, texts: List[str]) -> List[List[float]]:
        """
        Async version of embed_documents.

        For now, falls back to sync implementation.
        TODO: Implement proper async with httpx.AsyncClient
        """
        return self.embed_documents(texts)

    async def aembed_query(self, text: str) -> List[float]:
        """
        Async version of embed_query.

        For now, falls back to sync implementation.
        TODO: Implement proper async with httpx.AsyncClient
        """
        return self.embed_query(text)

    def close(self) -> None:
        """Close the HTTP client."""
        if self._client is not None:
            self._client.close()
            self._client = None

    def __del__(self):
        """Cleanup on deletion."""
        self.close()
