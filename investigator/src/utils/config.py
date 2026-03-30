"""Configuration management using Pydantic Settings.

This module provides type-safe configuration loading from environment variables
and .env files. Uses Google AI Studio (Gemini) via the OpenAI-compatible endpoint.
"""

from pathlib import Path

from pydantic import Field, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Config(BaseSettings):
    """Application configuration loaded from environment variables and .env file.

    All configuration values can be set via environment variables or a .env file.
    Required fields will raise a ValidationError if not provided.
    """

    # Google AI Studio (Gemini) API Configuration
    gemini_api_key: str = Field(
        ..., description="Google AI Studio API key for Gemini model access", min_length=1
    )

    # LangSmith Configuration (for evaluation and tracing)
    langsmith_api_key: str | None = Field(
        default=None,
        description="LangSmith API key for evaluation and tracing (optional)",
    )

    langsmith_project: str = Field(
        default="investigator-agent",
        description="LangSmith project name for organising traces and experiments",
    )

    # Model Configuration — Gemini via OpenAI-compatible endpoint
    model_name: str = Field(
        default="gemini-1.5-flash",
        description="Gemini model name to use via the OpenAI-compatible endpoint",
    )

    temperature: float = Field(
        default=0.0,
        description="Model temperature (0.0 = deterministic, 1.0 = creative)",
        ge=0.0,
        le=1.0,
    )

    max_tokens: int = Field(
        default=4096,
        description="Maximum tokens in model response",
        gt=0,
        le=8192,
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
        """Convert string to Path object."""
        return Path(v) if isinstance(v, str) else v

    def ensure_trace_directory_exists(self) -> None:
        """Create trace output directory if it does not exist."""
        self.trace_output_dir.mkdir(parents=True, exist_ok=True)


def load_config() -> Config:
    """Load configuration from environment variables and .env file.

    Returns:
        Config: Validated configuration object

    Raises:
        ValidationError: If required fields are missing or invalid
    """
    return Config()
