"""Configuration management using Pydantic Settings.

This module provides type-safe configuration loading from environment variables
and .env files.
"""

from pathlib import Path

from pydantic import Field, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Config(BaseSettings):
    """Application configuration loaded from environment variables and .env file.

    All configuration values can be set via environment variables or a .env file.
    Required fields will raise a ValidationError if not provided.
    """

    # Anthropic API Configuration
    anthropic_api_key: str = Field(
        ..., description="Anthropic API key for Claude model access", min_length=1
    )

    # LangSmith Configuration (for evaluation and tracing)
    langsmith_api_key: str | None = Field(
        default=None,
        description="LangSmith API key for evaluation and tracing (optional)",
    )

    langsmith_project: str = Field(
        default="investigator-agent",
        description="LangSmith project name for organizing traces and experiments",
    )

    # Model Configuration
    model_name: str = Field(
        default="claude-sonnet-4-5", description="Claude model name to use"
    )

    temperature: float = Field(
        default=0.0,
        description="Model temperature (0.0 = deterministic, 1.0 = creative)",
        ge=0.0,
        le=1.0,
    )

    max_tokens: int = Field(
        default=4096, description="Maximum tokens in model response", gt=0, le=8192
    )

    # Observability Configuration
    trace_output_dir: Path = Field(
        default=Path("traces"),
        description="Directory for OpenTelemetry trace JSON files",
    )

    # Retry Configuration
    llm_max_retry_attempts: int = Field(
        default=3,
        description="Maximum retry attempts for LLM API calls",
        gt=0,
        le=10,
    )

    llm_retry_exponential_jitter: bool = Field(
        default=True,
        description="Enable exponential backoff with jitter for LLM retries",
    )

    tool_max_retry_attempts: int = Field(
        default=3,
        description="Maximum retry attempts for tool execution",
        gt=0,
        le=10,
    )

    tool_retry_exponential_jitter: bool = Field(
        default=True,
        description="Enable exponential backoff with jitter for tool retries",
    )

    model_config = SettingsConfigDict(
        env_file=".env", env_file_encoding="utf-8", case_sensitive=False, extra="ignore"
    )

    @field_validator("trace_output_dir", mode="before")
    @classmethod
    def validate_trace_output_dir(cls, v: str | Path) -> Path:
        """Convert string to Path and create directory if it doesn't exist."""
        path = Path(v) if isinstance(v, str) else v
        return path

    def ensure_trace_directory_exists(self) -> None:
        """Create trace output directory if it doesn't exist."""
        self.trace_output_dir.mkdir(parents=True, exist_ok=True)


def load_config() -> Config:
    """Load configuration from environment variables and .env file.

    Returns:
        Config: Validated configuration object

    Raises:
        ValidationError: If required fields are missing or invalid
    """
    return Config()
