"""Configuration management for Discord bots."""

import json
import os
from enum import Enum
from pathlib import Path

from pydantic import Field, field_validator
from pydantic_settings import BaseSettings


class BotType(str, Enum):
    """Bot type enumeration."""
    CLIPPY = "clippy"
    MUSIC = "music"
    MTG = "mtg"


class BotConfig(BaseSettings):
    """Unified configuration for Discord bots."""

    # Bot identification
    bot_type: BotType
    bot_name: str = ""
    discord_token: str = ""
    command_prefix: str = "!"

    # Server configuration (removed guild_id - using global commands only)

    # Behavior settings
    debug_mode: bool = False
    log_level: str = "info"
    json_logging: bool = False
    command_cooldown: float = 3.0  # seconds
    shutdown_timeout: float = 30.0  # seconds
    request_timeout: float = 30.0  # seconds
    max_retries: int = 3

    # Feature flags
    random_responses: bool = False
    random_interval: float = 2700.0  # 45 minutes in seconds
    random_message_delay: float = 3.0  # seconds

    # Cache settings
    cache_ttl: float = 3600.0  # 1 hour in seconds
    cache_size: int = 1000

    # Music bot specific settings
    max_queue_size: int = 100
    inactivity_timeout: float = 300.0  # 5 minutes in seconds
    volume_level: float = 0.5

    # Database settings
    database_url: str = ""

    @field_validator('log_level')
    @classmethod
    def validate_log_level(cls, v: str) -> str:
        """Validate log level."""
        valid_levels = {'debug', 'info', 'warn', 'warning', 'error'}
        if v.lower() not in valid_levels:
            raise ValueError(f"Invalid log level: {v}. Must be one of {valid_levels}")
        return v.lower()

    @field_validator('volume_level')
    @classmethod
    def validate_volume_level(cls, v: float) -> float:
        """Validate volume level is between 0 and 1."""
        if not 0 <= v <= 1:
            raise ValueError("Volume level must be between 0 and 1")
        return v

    def validate_config(self) -> None:
        """Validate the configuration after loading."""
        if not self.discord_token:
            token_name = f"{self.bot_type.value.upper()}_DISCORD_TOKEN"
            raise ValueError(f"{self.bot_type} bot: {token_name} is required")

        if not self.bot_name:
            raise ValueError(f"{self.bot_type} bot: bot_name is required")

        if self.shutdown_timeout <= 0:
            raise ValueError(f"{self.bot_type} bot: shutdown_timeout must be positive")

        if self.request_timeout <= 0:
            raise ValueError(f"{self.bot_type} bot: request_timeout must be positive")

        if self.max_retries < 0:
            raise ValueError(f"{self.bot_type} bot: max_retries cannot be negative")

        # Bot-specific validation
        if self.bot_type == BotType.MUSIC:
            if self.max_queue_size <= 0:
                self.max_queue_size = 100
            if self.inactivity_timeout <= 0:
                self.inactivity_timeout = 300.0

        elif self.bot_type == BotType.MTG:
            if self.cache_ttl <= 0:
                raise ValueError("MTG bot: cache_ttl must be positive")
            if self.cache_size <= 0:
                raise ValueError("MTG bot: cache_size must be positive")


class ClippyConfig(BotConfig):
    """Configuration for Clippy bot."""

    bot_type: BotType = Field(default=BotType.CLIPPY, init=False)
    bot_name: str = "Clippy Bot"
    command_cooldown: float = 5.0
    random_responses: bool = True
    random_interval: float = 2700.0  # 45 minutes
    random_message_delay: float = 3.0

    class Config:
        env_prefix = "CLIPPY_"


class MusicConfig(BotConfig):
    """Configuration for Music bot."""

    bot_type: BotType = Field(default=BotType.MUSIC, init=False)
    bot_name: str = "Music Bot"
    command_cooldown: float = 3.0
    max_queue_size: int = 100
    inactivity_timeout: float = 300.0  # 5 minutes
    volume_level: float = 0.5
    database_url: str = "music.db"

    class Config:
        env_prefix = "MUSIC_"


class MTGConfig(BotConfig):
    """Configuration for MTG Card bot."""

    bot_type: BotType = Field(default=BotType.MTG, init=False)
    bot_name: str = "MTG Card Bot"
    command_cooldown: float = 2.0
    cache_ttl: float = 3600.0  # 1 hour
    cache_size: int = 1000

    class Config:
        env_prefix = "MTG_"


def load_config(bot_type: BotType, config_path: str | None = None) -> BotConfig:
    """Load configuration for a specific bot type."""
    # Get the appropriate config class
    config_classes = {
        BotType.CLIPPY: ClippyConfig,
        BotType.MUSIC: MusicConfig,
        BotType.MTG: MTGConfig,
    }

    config_class = config_classes[bot_type]

    # Load from file if provided
    file_config = {}
    if config_path and Path(config_path).exists():
        with open(config_path) as f:
            file_config = json.load(f)

    # Create config instance (pydantic-settings handles env vars automatically)
    config = config_class(**file_config)

    # Override with common environment variables
    if os.getenv("COMMAND_PREFIX"):
        config.command_prefix = os.getenv("COMMAND_PREFIX")
    if os.getenv("LOG_LEVEL"):
        config.log_level = os.getenv("LOG_LEVEL").lower()
    if os.getenv("DEBUG"):
        config.debug_mode = os.getenv("DEBUG").lower() in ("true", "1", "yes")
    if os.getenv("JSON_LOGGING"):
        config.json_logging = os.getenv("JSON_LOGGING").lower() in ("true", "1", "yes")
    if os.getenv("SHUTDOWN_TIMEOUT"):
        try:
            config.shutdown_timeout = float(os.getenv("SHUTDOWN_TIMEOUT").rstrip('s'))
        except (ValueError, AttributeError):
            pass
    if os.getenv("REQUEST_TIMEOUT"):
        try:
            config.request_timeout = float(os.getenv("REQUEST_TIMEOUT").rstrip('s'))
        except (ValueError, AttributeError):
            pass
    if os.getenv("MAX_RETRIES"):
        try:
            config.max_retries = int(os.getenv("MAX_RETRIES"))
        except (ValueError, TypeError):
            pass

    # Validate the final configuration
    config.validate_config()

    return config


def get_bool(key: str, default: bool = False) -> bool:
    """Get boolean environment variable with default."""
    value = os.getenv(key)
    if value is None:
        return default
    return value.lower() in ("true", "1", "yes", "on")


def get_int(key: str, default: int = 0) -> int:
    """Get integer environment variable with default."""
    value = os.getenv(key)
    if value is None:
        return default
    try:
        return int(value)
    except ValueError:
        return default


def get_string(key: str, default: str = "") -> str:
    """Get string environment variable with default."""
    return os.getenv(key, default)


def get_float(key: str, default: float = 0.0) -> float:
    """Get float environment variable with default."""
    value = os.getenv(key)
    if value is None:
        return default
    try:
        return float(value)
    except ValueError:
        return default


def load_env_file(env_file: Path) -> None:
    """Load environment variables from .env file if it exists."""
    if not env_file.exists():
        return

    with open(env_file) as f:
        for line in f:
            line = line.strip()
            if line == "" or line.startswith("#"):
                continue

            if "=" in line:
                key, value = line.split("=", 1)
                key = key.strip()
                value = value.strip()

                # Remove quotes if present
                if (value.startswith('"') and value.endswith('"')) or \
                   (value.startswith("'") and value.endswith("'")):
                    value = value[1:-1]

                # Only set if not already set by system environment
                if not os.getenv(key):
                    os.environ[key] = value
