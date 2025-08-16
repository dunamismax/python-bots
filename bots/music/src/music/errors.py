"""Simple error handling for Music bot."""

from enum import Enum
from typing import Any


class ErrorType(str, Enum):
    """Error type enumeration."""
    API = "api_error"
    NOT_FOUND = "not_found_error"
    RATE_LIMIT = "rate_limit_error"
    NETWORK = "network_error"
    VALIDATION = "validation_error"
    UNKNOWN = "unknown_error"
    DEPENDENCY = "dependency_error"
    PERMISSION = "permission_error"
    AUDIO = "audio_error"


class MusicError(Exception):
    """Music bot specific error."""

    def __init__(self, error_type: ErrorType, message: str, cause: Exception = None):
        self.error_type = error_type
        self.message = message
        self.cause = cause
        super().__init__(message)


def create_error(error_type: ErrorType, message: str, cause: Exception = None) -> MusicError:
    """Create a MusicError with the given type and message."""
    return MusicError(error_type, message, cause)