"""Unit tests for configuration management."""

import os
from pathlib import Path
from typing import Generator

import pytest
from pydantic import ValidationError

from src.utils.config import Config, load_config


@pytest.fixture
def clean_env() -> Generator[None, None, None]:
    """Clear environment variables before and after tests."""
    # Save original environment
    original_env = os.environ.copy()

    # Clear config-related env vars
    config_vars = [
        "ANTHROPIC_API_KEY",
        "MODEL_NAME",
        "TEMPERATURE",
        "MAX_TOKENS",
        "TRACE_OUTPUT_DIR",
    ]
    for var in config_vars:
        os.environ.pop(var, None)

    yield

    # Restore original environment
    os.environ.clear()
    os.environ.update(original_env)


@pytest.fixture
def valid_env_config(clean_env: None) -> None:
    """Set up valid environment configuration."""
    os.environ["ANTHROPIC_API_KEY"] = "test-api-key-123"
    os.environ["MODEL_NAME"] = "claude-sonnet-4-5"
    os.environ["TEMPERATURE"] = "0.0"
    os.environ["MAX_TOKENS"] = "4096"
    os.environ["TRACE_OUTPUT_DIR"] = "test_traces"


def test_config_loads_from_env(valid_env_config: None) -> None:
    """Test that configuration loads from environment variables."""
    config = Config()

    assert config.anthropic_api_key == "test-api-key-123"
    assert config.model_name == "claude-sonnet-4-5"
    assert config.temperature == 0.0
    assert config.max_tokens == 4096
    assert config.trace_output_dir == Path("test_traces")


def test_config_missing_required_api_key(clean_env: None) -> None:
    """Test that missing ANTHROPIC_API_KEY raises ValidationError."""
    # Temporarily rename .env file to prevent it from being loaded
    env_file = Path(".env")
    env_backup = Path(".env.backup_for_test")
    env_exists = env_file.exists()
    
    if env_exists:
        env_file.rename(env_backup)
    
    try:
        with pytest.raises(ValidationError) as exc_info:
            Config()

        errors = exc_info.value.errors()
        assert len(errors) > 0
        assert any(error["loc"] == ("anthropic_api_key",) for error in errors)
        assert any("Field required" in str(error["msg"]) for error in errors)
    finally:
        # Restore .env file
        if env_exists and env_backup.exists():
            env_backup.rename(env_file)


def test_config_empty_api_key(clean_env: None) -> None:
    """Test that empty ANTHROPIC_API_KEY raises ValidationError."""
    os.environ["ANTHROPIC_API_KEY"] = ""

    with pytest.raises(ValidationError) as exc_info:
        Config()

    errors = exc_info.value.errors()
    assert any(error["loc"] == ("anthropic_api_key",) for error in errors)


def test_config_default_values(clean_env: None) -> None:
    """Test that default values are applied when not specified."""
    # Temporarily rename .env file to test defaults
    env_file = Path(".env")
    env_backup = Path(".env.backup_for_test")
    env_exists = env_file.exists()
    
    if env_exists:
        env_file.rename(env_backup)
    
    try:
        os.environ["ANTHROPIC_API_KEY"] = "test-api-key-123"

        config = Config()

        assert config.model_name == "claude-sonnet-4-5"
        assert config.temperature == 0.0
        assert config.max_tokens == 4096
        assert config.trace_output_dir == Path("traces")
    finally:
        # Restore .env file
        if env_exists and env_backup.exists():
            env_backup.rename(env_file)


def test_config_temperature_validation(clean_env: None) -> None:
    """Test that temperature is validated to be between 0.0 and 1.0."""
    os.environ["ANTHROPIC_API_KEY"] = "test-api-key-123"

    # Test too low
    os.environ["TEMPERATURE"] = "-0.1"
    with pytest.raises(ValidationError) as exc_info:
        Config()
    errors = exc_info.value.errors()
    assert any(error["loc"] == ("temperature",) for error in errors)

    # Test too high
    os.environ["TEMPERATURE"] = "1.1"
    with pytest.raises(ValidationError) as exc_info:
        Config()
    errors = exc_info.value.errors()
    assert any(error["loc"] == ("temperature",) for error in errors)

    # Test valid boundary values
    os.environ["TEMPERATURE"] = "0.0"
    config = Config()
    assert config.temperature == 0.0

    os.environ["TEMPERATURE"] = "1.0"
    config = Config()
    assert config.temperature == 1.0


def test_config_max_tokens_validation(clean_env: None) -> None:
    """Test that max_tokens is validated to be positive and within limits."""
    os.environ["ANTHROPIC_API_KEY"] = "test-api-key-123"

    # Test zero (not allowed)
    os.environ["MAX_TOKENS"] = "0"
    with pytest.raises(ValidationError) as exc_info:
        Config()
    errors = exc_info.value.errors()
    assert any(error["loc"] == ("max_tokens",) for error in errors)

    # Test negative (not allowed)
    os.environ["MAX_TOKENS"] = "-100"
    with pytest.raises(ValidationError) as exc_info:
        Config()
    errors = exc_info.value.errors()
    assert any(error["loc"] == ("max_tokens",) for error in errors)

    # Test too high
    os.environ["MAX_TOKENS"] = "10000"
    with pytest.raises(ValidationError) as exc_info:
        Config()
    errors = exc_info.value.errors()
    assert any(error["loc"] == ("max_tokens",) for error in errors)

    # Test valid value
    os.environ["MAX_TOKENS"] = "4096"
    config = Config()
    assert config.max_tokens == 4096


def test_config_trace_output_dir_as_path(clean_env: None) -> None:
    """Test that trace_output_dir is converted to Path object."""
    os.environ["ANTHROPIC_API_KEY"] = "test-api-key-123"
    os.environ["TRACE_OUTPUT_DIR"] = "custom/traces/dir"

    config = Config()

    assert isinstance(config.trace_output_dir, Path)
    assert config.trace_output_dir == Path("custom/traces/dir")


def test_config_case_insensitive(clean_env: None) -> None:
    """Test that environment variables are case-insensitive."""
    os.environ["anthropic_api_key"] = "test-api-key-lowercase"
    os.environ["model_name"] = "test-model"

    config = Config()

    assert config.anthropic_api_key == "test-api-key-lowercase"
    assert config.model_name == "test-model"


def test_load_config(valid_env_config: None) -> None:
    """Test that load_config() function works correctly."""
    config = load_config()

    assert isinstance(config, Config)
    assert config.anthropic_api_key == "test-api-key-123"
    assert config.model_name == "claude-sonnet-4-5"


def test_ensure_trace_directory_exists(valid_env_config: None, tmp_path: Path) -> None:
    """Test that ensure_trace_directory_exists creates the directory."""
    os.environ["TRACE_OUTPUT_DIR"] = str(tmp_path / "test_traces")

    config = Config()

    # Directory shouldn't exist yet
    assert not config.trace_output_dir.exists()

    # Create it
    config.ensure_trace_directory_exists()

    # Now it should exist
    assert config.trace_output_dir.exists()
    assert config.trace_output_dir.is_dir()


def test_ensure_trace_directory_exists_idempotent(
    valid_env_config: None, tmp_path: Path
) -> None:
    """Test that ensure_trace_directory_exists can be called multiple times safely."""
    os.environ["TRACE_OUTPUT_DIR"] = str(tmp_path / "test_traces")

    config = Config()

    # Create directory multiple times
    config.ensure_trace_directory_exists()
    config.ensure_trace_directory_exists()
    config.ensure_trace_directory_exists()

    # Should still exist and be a directory
    assert config.trace_output_dir.exists()
    assert config.trace_output_dir.is_dir()


def test_config_ignores_extra_env_vars(clean_env: None) -> None:
    """Test that extra environment variables are ignored."""
    os.environ["ANTHROPIC_API_KEY"] = "test-api-key-123"
    os.environ["UNKNOWN_CONFIG_VAR"] = "should-be-ignored"
    os.environ["ANOTHER_RANDOM_VAR"] = "also-ignored"

    # Should not raise an error
    config = Config()

    assert config.anthropic_api_key == "test-api-key-123"
    assert not hasattr(config, "unknown_config_var")
    assert not hasattr(config, "another_random_var")
