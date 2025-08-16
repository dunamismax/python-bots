"""Unified structured logging functionality for Discord bots."""

import logging
import time
from typing import Any

import structlog
from structlog.types import EventDict, Processor

from .errors import BotError

# Global logger instance
default_logger: structlog.BoundLogger | None = None


def timestamp_processor(logger: Any, method_name: str, event_dict: EventDict) -> EventDict:
    """Add timestamp to log events."""
    import datetime
    now = datetime.datetime.now(datetime.timezone.utc)
    event_dict["timestamp"] = now.isoformat()
    return event_dict


def level_processor(logger: Any, method_name: str, event_dict: EventDict) -> EventDict:
    """Add log level to event dict."""
    event_dict["level"] = method_name
    return event_dict


def initialize_logger(level: str = "info", json_format: bool = False) -> None:
    """Initialize the global logger with the specified level and format."""
    global default_logger

    # Convert level string to logging level
    level_map = {
        "debug": logging.DEBUG,
        "info": logging.INFO,
        "warn": logging.WARNING,
        "warning": logging.WARNING,
        "error": logging.ERROR,
    }
    log_level = level_map.get(level.lower(), logging.INFO)

    # Configure structlog
    processors: list[Processor] = [
        structlog.contextvars.merge_contextvars,
        structlog.processors.add_log_level,
        structlog.processors.StackInfoRenderer(),
        timestamp_processor,
    ]

    if json_format:
        processors.append(structlog.processors.JSONRenderer())
    else:
        processors.append(structlog.dev.ConsoleRenderer(colors=True))

    structlog.configure(
        processors=processors,
        wrapper_class=structlog.make_filtering_bound_logger(log_level),
        logger_factory=structlog.PrintLoggerFactory(),
        cache_logger_on_first_use=True,
    )

    default_logger = structlog.get_logger()


def get_logger() -> structlog.BoundLogger:
    """Get the default logger."""
    if default_logger is None:
        initialize_logger()
    return default_logger


def with_context(**kwargs: Any) -> structlog.BoundLogger:
    """Return a logger with context values."""
    return get_logger().bind(**kwargs)


def with_component(component: str) -> structlog.BoundLogger:
    """Return a logger with a component field."""
    return get_logger().bind(component=component)


def with_bot(bot_name: str, bot_type: str) -> structlog.BoundLogger:
    """Return a logger with bot-specific information."""
    return get_logger().bind(bot_name=bot_name, bot_type=bot_type)


def with_user(user_id: str, username: str) -> structlog.BoundLogger:
    """Return a logger with user information."""
    return get_logger().bind(user_id=user_id, username=username)


def with_command(command: str) -> structlog.BoundLogger:
    """Return a logger with command information."""
    return get_logger().bind(command=command)


def with_duration(operation: str, duration_ms: float) -> structlog.BoundLogger:
    """Return a logger with duration information."""
    return get_logger().bind(operation=operation, duration_ms=duration_ms)


def log_error(logger: structlog.BoundLogger, error: Exception, message: str) -> None:
    """Log a BotError with appropriate structured fields."""
    if isinstance(error, BotError):
        context = {
            "error_type": error.get_type(),
            "error_message": str(error),
            **error.get_context(),
        }
        logger.error(message, **context)
    else:
        logger.error(message, error=str(error), error_type=type(error).__name__)


def debug(message: str, **kwargs: Any) -> None:
    """Log a debug message."""
    get_logger().debug(message, **kwargs)


def info(message: str, **kwargs: Any) -> None:
    """Log an info message."""
    get_logger().info(message, **kwargs)


def warning(message: str, **kwargs: Any) -> None:
    """Log a warning message."""
    get_logger().warning(message, **kwargs)


def error(message: str, **kwargs: Any) -> None:
    """Log an error message."""
    get_logger().error(message, **kwargs)


def log_startup(
    bot_name: str,
    bot_type: str,
    prefix: str,
    log_level: str,
    debug_mode: bool,
) -> None:
    """Log application startup information."""
    logger = with_bot(bot_name, bot_type)
    logger.info(
        "Starting Discord bot",
        command_prefix=prefix,
        log_level=log_level,
        debug_mode=debug_mode,
    )


def log_shutdown(bot_name: str, bot_type: str) -> None:
    """Log application shutdown information."""
    logger = with_bot(bot_name, bot_type)
    logger.info("Bot shutdown complete")


def log_api_request(
    service: str,
    endpoint: str,
    duration_ms: float,
    success: bool,
) -> None:
    """Log API request information."""
    logger = with_component(service)
    logger.debug(
        "API request completed",
        endpoint=endpoint,
        duration_ms=duration_ms,
        success=success,
    )


def log_discord_command(
    user_id: str,
    username: str,
    command: str,
    success: bool,
) -> None:
    """Log Discord command execution."""
    logger = with_component("discord").bind(
        user_id=user_id,
        username=username,
        command=command,
        success=success,
    )

    if success:
        logger.info("Command executed successfully")
    else:
        logger.warning("Command execution failed")


def log_cache_operation(
    operation: str,
    key: str,
    hit: bool,
    duration_ms: float,
) -> None:
    """Log cache operations with performance metrics."""
    logger = with_component("cache")
    logger.debug(
        "Cache operation",
        operation=operation,
        key=key,
        hit=hit,
        duration_ms=duration_ms,
    )




def log_security_event(
    event: str,
    user_id: str,
    reason: str,
    severity: str = "info",
) -> None:
    """Log security-related events."""
    logger = with_component("security")

    # Map severity to log level
    severity_map = {
        "critical": "error",
        "high": "error",
        "medium": "warning",
        "warn": "warning",
        "low": "info",
        "info": "info",
    }

    log_level = severity_map.get(severity.lower(), "info")
    log_func = getattr(logger, log_level)

    log_func(
        "Security event",
        event=event,
        user_id=user_id,
        reason=reason,
        severity=severity,
    )
