"""Pytest configuration and fixtures for Theo Agent tests."""

import os
from collections.abc import Generator

import pytest


def pytest_configure(config: pytest.Config) -> None:
    """Register custom markers."""
    config.addinivalue_line(
        "markers",
        "integration: marks tests as integration tests (may require external services)",
    )


@pytest.fixture
def clean_env() -> Generator[None, None, None]:
    """Fixture to provide a clean environment without OpenRouter variables."""
    # Store original values
    original_env = {}
    env_vars = ["OPENROUTER_API_KEY", "OPENROUTER_MODEL", "OPENROUTER_BASE_URL"]

    for var in env_vars:
        if var in os.environ:
            original_env[var] = os.environ.pop(var)

    yield

    # Restore original values
    for var in env_vars:
        if var in original_env:
            os.environ[var] = original_env[var]
        elif var in os.environ:
            del os.environ[var]


@pytest.fixture
def env_with_api_key(clean_env: None) -> Generator[str, None, None]:
    """Fixture to provide environment with a test API key."""
    test_key = "test-api-key-12345"
    os.environ["OPENROUTER_API_KEY"] = test_key
    yield test_key
    if "OPENROUTER_API_KEY" in os.environ:
        del os.environ["OPENROUTER_API_KEY"]
