"""Tests for Theo Agent configuration module.

These tests verify that the Pydantic settings configuration correctly loads
from environment variables and validates required fields.
"""

import os

import pytest
from pydantic import ValidationError


class TestOpenRouterConfig:
    """Tests for OpenRouter configuration via Pydantic settings."""

    def test_config_loads_api_key_from_environment(self, env_with_api_key: str) -> None:
        """Test that OPENROUTER_API_KEY is loaded from environment."""
        # Import here to ensure fresh config load after env is set
        from theo.config import Settings

        settings = Settings()
        assert settings.openrouter_api_key == env_with_api_key

    def test_missing_api_key_raises_validation_error(self, clean_env: None) -> None:
        """Test that missing OPENROUTER_API_KEY raises ValidationError."""
        from theo.config import Settings

        with pytest.raises(ValidationError) as exc_info:
            Settings()

        # Verify the error mentions the API key field
        errors = exc_info.value.errors()
        assert len(errors) == 1
        assert errors[0]["loc"] == ("api_key",)
        # Check for "missing" type or "required" in the message
        error_type = errors[0]["type"].lower()
        error_msg = errors[0]["msg"].lower()
        assert "missing" in error_type or "required" in error_msg

    def test_default_model_configuration(self, env_with_api_key: str) -> None:
        """Test that default model is set to arcee-ai/trinity-mini."""
        from theo.config import Settings

        settings = Settings()
        assert settings.openrouter_model == "arcee-ai/trinity-mini"

    def test_custom_model_override_from_environment(self, env_with_api_key: str) -> None:
        """Test that OPENROUTER_MODEL env var overrides default model."""
        custom_model = "anthropic/claude-3-opus"
        os.environ["OPENROUTER_MODEL"] = custom_model

        try:
            from theo.config import Settings

            settings = Settings()
            assert settings.openrouter_model == custom_model
        finally:
            del os.environ["OPENROUTER_MODEL"]

    def test_default_base_url_configuration(self, env_with_api_key: str) -> None:
        """Test that default base URL is set to OpenRouter API endpoint."""
        from theo.config import Settings

        settings = Settings()
        assert settings.openrouter_base_url == "https://openrouter.ai/api/v1"

    def test_custom_base_url_override_from_environment(self, env_with_api_key: str) -> None:
        """Test that OPENROUTER_BASE_URL env var overrides default base URL."""
        custom_url = "https://custom.api.endpoint/v1"
        os.environ["OPENROUTER_BASE_URL"] = custom_url

        try:
            from theo.config import Settings

            settings = Settings()
            assert settings.openrouter_base_url == custom_url
        finally:
            del os.environ["OPENROUTER_BASE_URL"]
