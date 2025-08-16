"""Shared library for Python Discord bots."""

__version__ = "1.0.0"

# Export main modules
from . import config, database, discord_utils, errors, logging, security

__all__ = [
    "config",
    "database",
    "discord_utils",
    "errors",
    "logging",
    "security",
]
