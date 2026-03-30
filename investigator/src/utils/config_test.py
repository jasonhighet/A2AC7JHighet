"""Unit tests for configuration management."""

import pytest
from pydantic import ValidationError

from src.utils.config import Config, load_config


def test_config_requires_gemini_api_key():
    """Config raises ValidationError when GEMINI_API_KEY is missing."""
    with pytest.raises(ValidationError) as exc_info:
        Config(gemini_api_key="")  # type: ignore[call-arg]
    errors = exc_info.value.errors()
    assert any("gemini_api_key" in str(e) for e in errors)


def test_config_accepts_valid_api_key():
    """Config accepts a valid GEMINI_API_KEY."""
    config = Config(gemini_api_key="test-key-abc")
    assert config.gemini_api_key == "test-key-abc"


def test_config_default_model_name():
    """Default model is gemini-1.5-flash when no .env or env var overrides it."""
    # Subclass to disable .env loading — tests Pydantic field defaults only
    class IsolatedConfig(Config):
        model_config = Config.model_config.copy()

    IsolatedConfig.model_config["env_file"] = None  # type: ignore[index]

    config = IsolatedConfig(gemini_api_key="test-key")
    assert config.model_name == "gemini-1.5-flash"


def test_config_default_temperature():
    """Default temperature is 0.0."""
    config = Config(gemini_api_key="test-key")
    assert config.temperature == 0.0


def test_config_temperature_bounds():
    """Temperature must be between 0.0 and 1.0."""
    with pytest.raises(ValidationError):
        Config(gemini_api_key="test-key", temperature=1.5)
    with pytest.raises(ValidationError):
        Config(gemini_api_key="test-key", temperature=-0.1)


def test_config_default_max_tokens():
    """Default max_tokens is 4096."""
    config = Config(gemini_api_key="test-key")
    assert config.max_tokens == 4096


def test_config_max_tokens_bounds():
    """max_tokens must be positive and <= 8192."""
    with pytest.raises(ValidationError):
        Config(gemini_api_key="test-key", max_tokens=0)
    with pytest.raises(ValidationError):
        Config(gemini_api_key="test-key", max_tokens=9000)


def test_config_trace_output_dir_converts_string():
    """trace_output_dir accepts a string and converts to Path."""
    from pathlib import Path

    config = Config(gemini_api_key="test-key", trace_output_dir="my/traces")
    assert config.trace_output_dir == Path("my/traces")


def test_config_default_langsmith_project():
    """Default LangSmith project name is correct."""
    config = Config(gemini_api_key="test-key")
    assert config.langsmith_project == "investigator-agent"


def test_config_langsmith_api_key_optional():
    """LangSmith API key defaults to None when not set in .env or environment."""
    # Subclass to disable .env loading — tests Pydantic field defaults only
    class IsolatedConfig(Config):
        model_config = Config.model_config.copy()

    IsolatedConfig.model_config["env_file"] = None  # type: ignore[index]

    config = IsolatedConfig(gemini_api_key="test-key")
    assert config.langsmith_api_key is None


def test_config_retry_defaults():
    """Retry configuration defaults are sensible."""
    config = Config(gemini_api_key="test-key")
    assert config.llm_max_retry_attempts == 3
    assert config.llm_retry_exponential_jitter is True
    assert config.tool_max_retry_attempts == 3
    assert config.tool_retry_exponential_jitter is True


def test_config_retry_attempts_bounds():
    """Retry attempts must be between 1 and 10."""
    with pytest.raises(ValidationError):
        Config(gemini_api_key="test-key", llm_max_retry_attempts=0)
    with pytest.raises(ValidationError):
        Config(gemini_api_key="test-key", llm_max_retry_attempts=11)


def test_ensure_trace_directory_exists(tmp_path):
    """ensure_trace_directory_exists creates the directory."""
    config = Config(gemini_api_key="test-key", trace_output_dir=tmp_path / "traces")
    assert not config.trace_output_dir.exists()
    config.ensure_trace_directory_exists()
    assert config.trace_output_dir.exists()
