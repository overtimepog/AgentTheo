"""Configuration module for Theo Agent.

This module provides Pydantic-based settings management with environment
variable loading for OpenRouter API configuration.
"""

from pathlib import Path

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


def _find_env_file() -> Path | None:
    """Find .env file, checking parent directories.

    Looks for .env in:
    1. Current working directory
    2. Parent JailbreakStuff directory (for nested project structure)
    """
    # Check current directory first
    cwd_env = Path.cwd() / ".env"
    if cwd_env.exists():
        return cwd_env

    # Check parent directories up to 3 levels
    current = Path.cwd()
    for _ in range(3):
        parent = current.parent
        env_path = parent / ".env"
        if env_path.exists():
            return env_path
        current = parent

    return None


class Settings(BaseSettings):
    """Application settings loaded from environment variables.

    Environment Variables:
        OPENROUTER_API_KEY: Required. API key for OpenRouter authentication.
        OPENROUTER_MODEL: Optional. Model identifier (default: arcee-ai/trinity-mini).
        OPENROUTER_BASE_URL: Optional. API base URL (default: https://openrouter.ai/api/v1).

    The .env file is searched in:
    1. Current working directory
    2. Parent directories (up to 3 levels)
    3. /Users/overtime/Documents/GitHub/JailbreakStuff/.env (fallback)

    Example:
        >>> import os
        >>> os.environ["OPENROUTER_API_KEY"] = "your-api-key"
        >>> settings = Settings()
        >>> settings.openrouter_model
        'arcee-ai/trinity-mini'
    """

    model_config = SettingsConfigDict(
        env_prefix="OPENROUTER_",
        env_file=_find_env_file(),
        env_file_encoding="utf-8",
        extra="ignore",
    )

    # Field names map to OPENROUTER_<FIELD_NAME> env vars
    # api_key -> OPENROUTER_API_KEY
    # model -> OPENROUTER_MODEL
    # base_url -> OPENROUTER_BASE_URL
    api_key: str = Field(
        ...,
        description="API key for OpenRouter authentication",
    )

    model: str = Field(
        default="arcee-ai/trinity-mini",
        description="Model identifier for the LLM",
    )

    base_url: str = Field(
        default="https://openrouter.ai/api/v1",
        description="Base URL for the OpenRouter API",
    )

    # Convenience properties with openrouter_ prefix for clarity
    @property
    def openrouter_api_key(self) -> str:
        """API key for OpenRouter authentication."""
        return self.api_key

    @property
    def openrouter_model(self) -> str:
        """Model identifier for the LLM."""
        return self.model

    @property
    def openrouter_base_url(self) -> str:
        """Base URL for the OpenRouter API."""
        return self.base_url


def get_settings() -> Settings:
    """Factory function to create a Settings instance.

    Returns:
        Settings: Configuration settings loaded from environment.

    Raises:
        pydantic.ValidationError: If required environment variables are missing.
    """
    return Settings()
