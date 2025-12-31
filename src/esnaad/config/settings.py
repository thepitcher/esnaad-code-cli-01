"""Pydantic settings for Esnaad Code configuration."""

import json
from functools import lru_cache
from pathlib import Path
from typing import Any

from pydantic import BaseModel, Field, SecretStr
from pydantic_settings import BaseSettings, SettingsConfigDict

from esnaad.config.constants import (
    DEFAULT_LLM_TIMEOUT,
    DEFAULT_MAX_ITERATIONS,
    DEFAULT_MAX_RETRIES,
    DEFAULT_MAX_TOKENS,
    DEFAULT_MODEL,
    DEFAULT_SUBTASK_MAX_ITERATIONS,
    DEFAULT_SUBTASK_TIMEOUT,
    DEFAULT_TEMPERATURE,
    DEFAULT_TIMEOUT_SECONDS,
    MAX_CLARIFICATION_QUESTIONS,
    MAX_FILE_SIZE_BYTES,
    MAX_OUTPUT_CHARS,
    COMMAND_TIMEOUT,
    SEARCH_MAX_RESULTS,
)

# Default config directory and file
CONFIG_DIR = Path.home() / ".esnaad"
CONFIG_FILE = CONFIG_DIR / "config.json"


class LLMSettings(BaseModel):
    """LLM provider settings."""

    base_url: str = Field(
        default="http://localhost:3000/api",
        description="Base URL for OpenAI-compatible API",
    )
    api_key: SecretStr | None = Field(
        default=None,
        description="API key for authentication",
    )
    model: str = Field(
        default=DEFAULT_MODEL,
        description="Model name to use",
    )
    temperature: float = Field(
        default=DEFAULT_TEMPERATURE,
        ge=0.0,
        le=2.0,
        description="Temperature for generation",
    )
    max_tokens: int = Field(
        default=DEFAULT_MAX_TOKENS,
        gt=0,
        description="Maximum tokens to generate",
    )
    timeout: float = Field(
        default=DEFAULT_LLM_TIMEOUT,
        gt=0,
        description="Request timeout in seconds",
    )
    verify_ssl: bool = Field(
        default=True,
        description="Verify SSL/TLS certificates",
    )


class OrchestratorSettings(BaseModel):
    """Orchestrator agent settings."""

    max_iterations: int = Field(
        default=DEFAULT_MAX_ITERATIONS,
        gt=0,
        description="Maximum iterations for the main agent loop",
    )
    timeout_seconds: int = Field(
        default=DEFAULT_TIMEOUT_SECONDS,
        gt=0,
        description="Timeout for the entire task in seconds",
    )
    enable_clarifications: bool = Field(
        default=True,
        description="Enable interactive clarifications",
    )
    max_clarification_questions: int = Field(
        default=MAX_CLARIFICATION_QUESTIONS,
        gt=0,
        le=10,
        description="Maximum clarification questions",
    )


class SubAgentSettings(BaseModel):
    """Sub-agent settings."""

    max_iterations: int = Field(
        default=DEFAULT_SUBTASK_MAX_ITERATIONS,
        gt=0,
        description="Maximum iterations for sub-agent loops",
    )
    timeout_seconds: int = Field(
        default=DEFAULT_SUBTASK_TIMEOUT,
        gt=0,
        description="Timeout per subtask in seconds",
    )
    max_retries: int = Field(
        default=DEFAULT_MAX_RETRIES,
        ge=0,
        description="Maximum retries for failed subtasks",
    )


class ToolSettings(BaseModel):
    """Tool system settings."""

    max_file_size_bytes: int = Field(
        default=MAX_FILE_SIZE_BYTES,
        gt=0,
        description="Maximum file size to read (bytes)",
    )
    max_output_chars: int = Field(
        default=MAX_OUTPUT_CHARS,
        gt=0,
        description="Maximum output characters from tools",
    )
    command_timeout: int = Field(
        default=COMMAND_TIMEOUT,
        gt=0,
        description="Command execution timeout in seconds",
    )
    search_max_results: int = Field(
        default=SEARCH_MAX_RESULTS,
        gt=0,
        description="Maximum search results",
    )


class Settings(BaseSettings):
    """Main application settings."""

    model_config = SettingsConfigDict(
        env_prefix="ESNAAD_",
        env_file=".env",
        env_file_encoding="utf-8",
        env_nested_delimiter="__",
        extra="ignore",
    )

    # Core settings
    working_directory: Path = Field(
        default_factory=Path.cwd,
        description="Working directory for file operations",
    )
    config_dir: Path = Field(
        default_factory=lambda: Path.home() / ".esnaad",
        description="Configuration directory",
    )
    debug: bool = Field(
        default=False,
        description="Enable debug mode",
    )
    log_level: str = Field(
        default="INFO",
        description="Logging level",
    )

    # Component settings
    llm: LLMSettings = Field(default_factory=LLMSettings)
    orchestrator: OrchestratorSettings = Field(default_factory=OrchestratorSettings)
    subagent: SubAgentSettings = Field(default_factory=SubAgentSettings)
    tools: ToolSettings = Field(default_factory=ToolSettings)

    def model_post_init(self, __context: Any) -> None:
        """Ensure config directory exists."""
        self.config_dir.mkdir(parents=True, exist_ok=True)


def _load_config_file() -> dict[str, Any]:
    """Load configuration from JSON file if it exists."""
    if CONFIG_FILE.exists():
        try:
            with open(CONFIG_FILE, "r", encoding="utf-8") as f:
                return json.load(f)
        except (json.JSONDecodeError, IOError):
            return {}
    return {}


def _deep_merge(base: dict, override: dict) -> dict:
    """Deep merge two dictionaries."""
    result = base.copy()
    for key, value in override.items():
        if key in result and isinstance(result[key], dict) and isinstance(value, dict):
            result[key] = _deep_merge(result[key], value)
        else:
            result[key] = value
    return result


@lru_cache
def get_settings() -> Settings:
    """
    Get cached settings instance.

    Settings are loaded in this priority (later overrides earlier):
    1. Default values
    2. ~/.esnaad/config.json
    3. Environment variables (ESNAAD_*)
    """
    # Load from config file first
    config_data = _load_config_file()

    if config_data:
        # Create settings with config file data, env vars will override
        return Settings(**config_data)

    return Settings()


def save_config(config: dict[str, Any]) -> None:
    """
    Save configuration to ~/.esnaad/config.json.

    Args:
        config: Configuration dictionary to save
    """
    CONFIG_DIR.mkdir(parents=True, exist_ok=True)

    # Load existing config and merge
    existing = _load_config_file()
    merged = _deep_merge(existing, config)

    with open(CONFIG_FILE, "w", encoding="utf-8") as f:
        json.dump(merged, f, indent=2, default=str)


def get_config_path() -> Path:
    """Get the path to the config file."""
    return CONFIG_FILE


def load_project_settings(project_dir: Path) -> Settings:
    """
    Load settings with project-specific overrides.

    Looks for a .env file in the project directory and loads it.
    """
    project_env = project_dir / ".env"
    if project_env.exists():
        from dotenv import load_dotenv

        load_dotenv(project_env, override=True)
        # Clear cache to reload with new env vars
        get_settings.cache_clear()

    settings = get_settings()
    # Override working directory
    return Settings(working_directory=project_dir, **settings.model_dump(exclude={"working_directory"}))
