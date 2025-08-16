"""Configuration management for the MTG Card Discord bot."""

import os
from pathlib import Path


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


class MTGConfig:
    """Configuration for MTG Card bot."""

    def __init__(self):
        self.discord_token = os.getenv("MTG_DISCORD_TOKEN", "")
        self.bot_name = "MTG Card Bot"
        self.command_prefix = "!"
        self.log_level = os.getenv("LOG_LEVEL", "info").lower()
        self.json_logging = get_bool("JSON_LOGGING", False)
        self.debug_mode = get_bool("DEBUG", False)
        self.cache_ttl = get_float("MTG_CACHE_TTL", 3600.0)  # 1 hour
        self.cache_size = get_int("MTG_CACHE_SIZE", 1000)
        self.command_cooldown = get_float("MTG_COMMAND_COOLDOWN", 2.0)

    def validate_config(self) -> None:
        """Validate the configuration after loading."""
        if not self.discord_token:
            raise ValueError("MTG_DISCORD_TOKEN is required")

        if not self.bot_name:
            raise ValueError("bot_name is required")

        valid_levels = {'debug', 'info', 'warn', 'warning', 'error'}
        if self.log_level not in valid_levels:
            raise ValueError(f"Invalid log level: {self.log_level}. Must be one of {valid_levels}")

        if self.cache_ttl <= 0:
            raise ValueError("cache_ttl must be positive")
        
        if self.cache_size <= 0:
            raise ValueError("cache_size must be positive")


def load_config() -> MTGConfig:
    """Load configuration for MTG Card bot."""
    return MTGConfig()