"""Unified error handling for Discord bot applications."""

from enum import Enum
from typing import Any


class ErrorType(str, Enum):
    """Error type enumeration."""
    API_ERROR = "api_error"
    CONFIG_ERROR = "config_error"
    DISCORD_ERROR = "discord_error"
    VALIDATION_ERROR = "validation_error"
    NOT_FOUND_ERROR = "not_found_error"
    RATE_LIMIT_ERROR = "rate_limit_error"
    NETWORK_ERROR = "network_error"
    INTERNAL_ERROR = "internal_error"
    CACHE_ERROR = "cache_error"
    SECURITY_ERROR = "security_error"
    DATABASE_ERROR = "database_error"
    AUDIO_ERROR = "audio_error"
    PERMISSION_ERROR = "permission_error"


class BotError(Exception):
    """Categorized error with additional context."""

    def __init__(
        self,
        error_type: ErrorType,
        message: str,
        cause: Exception | None = None,
        status_code: int | None = None,
        context: dict[str, Any] | None = None,
    ):
        self.error_type = error_type
        self.message = message
        self.cause = cause
        self.status_code = status_code
        self.context_data = context or {}

        # Build the full error message
        if cause:
            full_message = f"{error_type}: {message} (caused by: {cause})"
        else:
            full_message = f"{error_type}: {message}"

        super().__init__(full_message)

    def get_type(self) -> str:
        """Get error type for logging."""
        return self.error_type.value

    def get_context(self) -> dict[str, Any]:
        """Get error context for logging."""
        return self.context_data.copy()

    def with_context(self, key: str, value: Any) -> "BotError":
        """Add context to the error."""
        self.context_data[key] = value
        return self

    def with_context_map(self, context: dict[str, Any]) -> "BotError":
        """Add multiple context values to the error."""
        self.context_data.update(context)
        return self


def new_api_error(message: str, cause: Exception | None = None) -> BotError:
    """Create a new API-related error."""
    return BotError(ErrorType.API_ERROR, message, cause)


def new_config_error(message: str, cause: Exception | None = None) -> BotError:
    """Create a new configuration error."""
    return BotError(ErrorType.CONFIG_ERROR, message, cause)


def new_discord_error(message: str, cause: Exception | None = None) -> BotError:
    """Create a new Discord-related error."""
    return BotError(ErrorType.DISCORD_ERROR, message, cause)


def new_validation_error(message: str) -> BotError:
    """Create a new validation error."""
    return BotError(ErrorType.VALIDATION_ERROR, message)


def new_not_found_error(message: str) -> BotError:
    """Create a new not found error."""
    return BotError(ErrorType.NOT_FOUND_ERROR, message)


def new_rate_limit_error(message: str, retry_after: int | None = None) -> BotError:
    """Create a new rate limit error."""
    context = {"retry_after": retry_after} if retry_after else None
    return BotError(ErrorType.RATE_LIMIT_ERROR, message, context=context)


def new_network_error(message: str, cause: Exception | None = None) -> BotError:
    """Create a new network error."""
    return BotError(ErrorType.NETWORK_ERROR, message, cause)


def new_internal_error(message: str, cause: Exception | None = None) -> BotError:
    """Create a new internal error."""
    return BotError(ErrorType.INTERNAL_ERROR, message, cause)


def new_cache_error(message: str, cause: Exception | None = None) -> BotError:
    """Create a new cache-related error."""
    return BotError(ErrorType.CACHE_ERROR, message, cause)


def new_security_error(message: str, cause: Exception | None = None) -> BotError:
    """Create a new security-related error."""
    return BotError(ErrorType.SECURITY_ERROR, message, cause)


def new_database_error(message: str, cause: Exception | None = None) -> BotError:
    """Create a new database error."""
    return BotError(ErrorType.DATABASE_ERROR, message, cause)


def new_audio_error(message: str, cause: Exception | None = None) -> BotError:
    """Create a new audio processing error."""
    return BotError(ErrorType.AUDIO_ERROR, message, cause)


def new_permission_error(message: str, cause: Exception | None = None) -> BotError:
    """Create a new permission error."""
    return BotError(ErrorType.PERMISSION_ERROR, message, cause)


def is_error_type(error: Exception, error_type: ErrorType) -> bool:
    """Check if an error is of a specific type."""
    return isinstance(error, BotError) and error.error_type == error_type


def from_http_status(status_code: int, message: str) -> BotError:
    """Create an appropriate error based on HTTP status code."""
    if status_code == 404:
        error_type = ErrorType.NOT_FOUND_ERROR
    elif status_code == 429:
        error_type = ErrorType.RATE_LIMIT_ERROR
    elif status_code in (401, 403):
        error_type = ErrorType.PERMISSION_ERROR
    elif 400 <= status_code < 500:
        error_type = ErrorType.VALIDATION_ERROR
    elif status_code >= 500:
        error_type = ErrorType.API_ERROR
    else:
        error_type = ErrorType.INTERNAL_ERROR

    return BotError(error_type, message, status_code=status_code)


def with_context(error: Exception, key: str, value: Any) -> Exception:
    """Add context to an existing error."""
    if isinstance(error, BotError):
        return error.with_context(key, value)

    # Convert regular error to BotError
    bot_error = new_internal_error(str(error), error)
    return bot_error.with_context(key, value)


def with_context_map(error: Exception, context: dict[str, Any]) -> Exception:
    """Add multiple context values to an existing error."""
    if isinstance(error, BotError):
        return error.with_context_map(context)

    # Convert regular error to BotError
    bot_error = new_internal_error(str(error), error)
    return bot_error.with_context_map(context)


def is_retryable(error: Exception) -> bool:
    """Determine if an error indicates a retryable condition."""
    if not isinstance(error, BotError):
        return False

    if error.error_type in (ErrorType.NETWORK_ERROR, ErrorType.API_ERROR, ErrorType.RATE_LIMIT_ERROR):
        return True

    if error.error_type == ErrorType.INTERNAL_ERROR:
        # Some internal errors might be retryable
        return error.status_code is None or error.status_code >= 500

    return False


def get_severity(error: Exception) -> str:
    """Get the severity level of an error."""
    if not isinstance(error, BotError):
        return "medium"

    severity_map = {
        ErrorType.SECURITY_ERROR: "high",
        ErrorType.PERMISSION_ERROR: "high",
        ErrorType.API_ERROR: "medium",
        ErrorType.DATABASE_ERROR: "medium",
        ErrorType.INTERNAL_ERROR: "medium",
        ErrorType.NETWORK_ERROR: "low",
        ErrorType.RATE_LIMIT_ERROR: "low",
        ErrorType.CACHE_ERROR: "low",
        ErrorType.VALIDATION_ERROR: "info",
        ErrorType.NOT_FOUND_ERROR: "info",
    }

    return severity_map.get(error.error_type, "medium")
