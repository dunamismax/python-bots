"""Shared Discord utilities and interfaces for all bot implementations."""

import re
import time
from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Any

import discord
from discord.ext import commands

from . import errors, logging
from .config import BotConfig


@dataclass
class BotInfo:
    """Information about a bot."""
    name: str
    type: str
    version: str = "2.0.0"
    start_time: float = 0.0
    is_connected: bool = False


class BotInterface(ABC):
    """Common interface that all bots must implement."""

    @abstractmethod
    async def start(self) -> None:
        """Start the bot."""
        pass

    @abstractmethod
    async def stop(self) -> None:
        """Stop the bot."""
        pass

    @abstractmethod
    def get_config(self) -> BotConfig:
        """Get the bot configuration."""
        pass

    @abstractmethod
    def get_bot_info(self) -> BotInfo:
        """Get information about the bot."""
        pass


class BaseBot(commands.Bot, BotInterface):
    """Base Discord bot with common functionality."""

    def __init__(self, config: BotConfig, intents: discord.Intents | None = None):
        # Validate configuration
        config.validate_config()

        # Discord intents
        if intents is None:
            intents = discord.Intents.default()
            intents.message_content = True
            intents.guilds = True
            intents.guild_messages = True

        # Initialize the commands.Bot
        super().__init__(
            command_prefix=config.command_prefix,
            intents=intents,
            case_insensitive=True,
        )

        self.config = config
        self.start_time = 0.0
        self.is_connected = False

        # Set up event handlers
        self.setup_events()

    def setup_events(self) -> None:
        """Set up default event handlers."""

        @self.event
        async def on_ready() -> None:
            """Handle bot ready event."""
            self.start_time = time.time()
            self.is_connected = True

            logger = logging.with_bot(self.config.bot_name, self.config.bot_type.value)
            logger.info(
                "Bot is ready",
                username=self.user.name if self.user else "Unknown",
                guilds=len(self.guilds),
            )

            # Set bot status
            status = f"Ready | {self.config.command_prefix}help"
            activity = discord.Game(name=status)
            await self.change_presence(activity=activity)

            logging.log_startup(
                self.config.bot_name,
                self.config.bot_type.value,
                self.config.command_prefix,
                self.config.log_level,
                self.config.debug_mode,
            )

        @self.event
        async def on_disconnect() -> None:
            """Handle disconnect event."""
            logger = logging.with_bot(self.config.bot_name, self.config.bot_type.value)
            logger.warning("Bot disconnected")
            self.is_connected = False


        @self.event
        async def on_command(ctx: commands.Context) -> None:
            """Handle command execution start."""
            # This is called when a command is about to be executed
            pass

        @self.event
        async def on_command_completion(ctx: commands.Context) -> None:
            """Handle successful command completion."""
            duration_ms = (time.time() - ctx.message.created_at.timestamp()) * 1000


            logging.log_discord_command(
                str(ctx.author.id),
                ctx.author.display_name,
                ctx.command.name if ctx.command else "unknown",
                True,
            )

        @self.event
        async def on_command_error(ctx: commands.Context, error: Exception) -> None:
            """Handle command errors."""
            duration_ms = (time.time() - ctx.message.created_at.timestamp()) * 1000


            logging.log_discord_command(
                str(ctx.author.id),
                ctx.author.display_name,
                ctx.command.name if ctx.command else "unknown",
                False,
            )

            await self.handle_command_error(ctx, error)

    async def start(self) -> None:
        """Start the Discord bot."""
        logger = logging.with_bot(self.config.bot_name, self.config.bot_type.value)
        logger.info("Starting Discord bot connection")

        try:
            await super().start(self.config.discord_token)
        except Exception as e:
            raise errors.new_discord_error("Failed to start Discord bot", e)

    async def stop(self) -> None:
        """Stop the Discord bot."""
        logger = logging.with_bot(self.config.bot_name, self.config.bot_type.value)
        logger.info("Stopping Discord bot")

        self.is_connected = False

        try:
            await self.close()
        except Exception as e:
            raise errors.new_discord_error("Failed to stop Discord bot", e)

        logging.log_shutdown(self.config.bot_name, self.config.bot_type.value)

    def get_config(self) -> BotConfig:
        """Get the bot configuration."""
        return self.config

    def get_bot_info(self) -> BotInfo:
        """Get information about the bot."""
        return BotInfo(
            name=self.config.bot_name,
            type=self.config.bot_type.value,
            start_time=self.start_time,
            is_connected=self.is_connected,
        )

    async def handle_command_error(self, ctx: commands.Context, error: Exception) -> None:
        """Handle command execution errors."""
        logger = logging.with_bot(self.config.bot_name, self.config.bot_type.value)
        logging.log_error(logger, error, "Command execution failed")

        # Don't send error messages to users for security errors
        if isinstance(error, errors.BotError) and error.error_type == errors.ErrorType.SECURITY_ERROR:
            logging.log_security_event("command_error", str(ctx.author.id), str(error), "medium")
            return

        # Handle different error types
        if isinstance(error, commands.CommandNotFound):
            message = f"❌ Unknown command. Use `{self.config.command_prefix}help` for available commands."
        elif isinstance(error, commands.MissingRequiredArgument):
            message = f"❌ Missing required argument. Use `{self.config.command_prefix}help {ctx.command}` for usage."
        elif isinstance(error, commands.BadArgument):
            message = "❌ Invalid argument provided."
        elif isinstance(error, commands.CommandOnCooldown):
            message = f"⏱️ Command is on cooldown. Try again in {error.retry_after:.1f} seconds."
        elif isinstance(error, commands.MissingPermissions):
            message = "🚫 You don't have permission to use this command."
        elif isinstance(error, commands.BotMissingPermissions):
            message = "🚫 I don't have the required permissions to execute this command."
        elif isinstance(error, errors.BotError):
            if error.error_type == errors.ErrorType.NOT_FOUND_ERROR:
                message = "❌ Not found. Try a different search."
            elif error.error_type == errors.ErrorType.VALIDATION_ERROR:
                message = f"❌ Invalid input. Use `{self.config.command_prefix}help` for usage."
            elif error.error_type == errors.ErrorType.RATE_LIMIT_ERROR:
                message = "⏱️ Rate limited. Please wait a moment before trying again."
            elif error.error_type == errors.ErrorType.PERMISSION_ERROR:
                message = "🚫 Permission denied."
            else:
                message = "❌ An error occurred. Please try again later."
        else:
            message = "❌ An unexpected error occurred. Please try again later."

        # Send error message to channel
        try:
            await ctx.send(message)
        except discord.HTTPException as e:
            logger.error("Failed to send error message", error=str(e))


def validate_input(input_text: str, max_length: int = 2000) -> None:
    """Validate and sanitize user input."""
    if not input_text.strip():
        raise errors.new_validation_error("Input cannot be empty")

    if len(input_text) > max_length:
        raise errors.new_validation_error(f"Input too long (max {max_length} characters)")

    # Basic security checks
    if contains_suspicious_content(input_text):
        raise errors.new_security_error("Suspicious input detected", None)


def contains_suspicious_content(input_text: str) -> bool:
    """Check for suspicious content in user input."""
    suspicious_patterns = [
        r'<script\b',
        r'javascript:',
        r'data:',
        r'file://',
        r'vbscript:',
        r'onload\s*=',
        r'onerror\s*=',
        r'@everyone',
        r'@here',
    ]

    text_lower = input_text.lower()
    for pattern in suspicious_patterns:
        if re.search(pattern, text_lower, re.IGNORECASE):
            return True

    return False


def create_embed(
    title: str,
    description: str = "",
    color: str = "blue",
    **kwargs: Any,
) -> discord.Embed:
    """Create a standardized Discord embed."""
    # Color mapping
    color_map = {
        "red": 0xFF0000,
        "error": 0xFF0000,
        "green": 0x00FF00,
        "success": 0x00FF00,
        "blue": 0x0000FF,
        "info": 0x0000FF,
        "yellow": 0xFFFF00,
        "warning": 0xFFFF00,
        "purple": 0x9932CC,
        "magic": 0x9932CC,
    }

    embed_color = color_map.get(color.lower(), 0x7289DA)  # Discord blurple as default

    embed = discord.Embed(
        title=title,
        description=description,
        color=embed_color,
        **kwargs,
    )

    return embed


async def send_typing(channel: discord.abc.Messageable) -> None:
    """Send typing indicator to channel."""
    try:
        await channel.typing()
    except discord.HTTPException:
        # Ignore typing errors
        pass


class CooldownManager:
    """Manage command cooldowns."""

    def __init__(self):
        self.cooldowns: dict[str, float] = {}

    def is_on_cooldown(self, key: str, cooldown_seconds: float) -> bool:
        """Check if a key is on cooldown."""
        now = time.time()
        if key in self.cooldowns:
            time_passed = now - self.cooldowns[key]
            return time_passed < cooldown_seconds
        return False

    def set_cooldown(self, key: str) -> None:
        """Set cooldown for a key."""
        self.cooldowns[key] = time.time()

    def clear_cooldown(self, key: str) -> None:
        """Clear cooldown for a key."""
        self.cooldowns.pop(key, None)


# Global cooldown manager
global_cooldown = CooldownManager()
