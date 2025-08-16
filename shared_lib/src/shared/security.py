"""Security utilities and validation for Discord bots."""

import html
import re
import secrets
import time
from urllib.parse import urlparse

from . import errors, logging


class InputValidator:
    """Comprehensive input validation."""

    def __init__(self, max_length: int = 2000):
        self.max_length = max_length
        self.blocked_patterns = [
            # XSS patterns
            "<script",
            "javascript:",
            "data:",
            "vbscript:",
            "onload=",
            "onerror=",
            "onclick=",
            "onmouseover=",

            # Code injection patterns
            "../",
            "..\\",
            "file://",
            "ftp://",

            # Discord mention abuse
            "@everyone",
            "@here",

            # SQL injection patterns (basic)
            "' or ",
            "' and ",
            "union select",
            "drop table",
            "delete from",
            "insert into",
            "update set",

            # Command injection
            "; rm ",
            "& rm ",
            "| rm ",
            "; del ",
            "& del ",
            "| del ",
            "$(rm",
            "`rm",

            # Path traversal
            "/etc/passwd",
            "/etc/shadow",
            "c:\\windows\\system32",

            # Potential token patterns
            "bot ",
            "bearer ",
            "oauth ",
        ]
        self.rate_limiter = RateLimiter(10, 60)  # 10 requests per minute per user

    def validate_input(self, input_text: str, user_id: str) -> None:
        """Perform comprehensive input validation."""
        # Rate limiting check
        if not self.rate_limiter.allow(user_id):
            logging.log_security_event("rate_limit_exceeded", user_id,
                                     "input validation rate limit exceeded", "medium")
            raise errors.new_rate_limit_error("Rate limit exceeded", 60)

        # Basic length check
        if not input_text.strip():
            raise errors.new_validation_error("Input cannot be empty")

        if len(input_text) > self.max_length:
            logging.log_security_event("input_too_long", user_id,
                                     "input exceeds maximum length", "low")
            raise errors.new_validation_error("Input too long")

        # Check for suspicious patterns
        self._check_suspicious_patterns(input_text, user_id)

        # Check for potential token exposure
        self._check_token_patterns(input_text, user_id)

        # URL validation if input contains URLs
        self._validate_urls(input_text, user_id)

    def _check_suspicious_patterns(self, input_text: str, user_id: str) -> None:
        """Check for malicious patterns."""
        text_lower = input_text.lower()

        for pattern in self.blocked_patterns:
            if pattern.lower() in text_lower:
                logging.log_security_event("suspicious_pattern_detected", user_id,
                                         f"blocked pattern: {pattern}", "high")
                raise errors.new_security_error("Suspicious content detected", None)

    def _check_token_patterns(self, input_text: str, user_id: str) -> None:
        """Check for potential token exposure."""
        # Discord token patterns (updated for 2025 formats)
        discord_token_patterns = [
            re.compile(r'[MN][A-Za-z\d]{23}\.[\w-]{6}\.[\w-]{27}'),  # Bot tokens
            re.compile(r'mfa\.[A-Za-z0-9_-]{20,}'),  # MFA tokens
            re.compile(r'[A-Za-z\d]{24}\.[A-Za-z\d]{6}\.[A-Za-z\d_-]{27}'),  # User tokens
        ]
        
        for pattern in discord_token_patterns:
            if pattern.search(input_text):
                logging.log_security_event("potential_token_exposure", user_id,
                                         "Discord token pattern detected", "critical")
                raise errors.new_security_error("Potential token exposure detected", None)

        # Generic secret patterns (long hex/base64 strings)
        secret_pattern = re.compile(r'[a-fA-F0-9]{32,}|[A-Za-z0-9+/]{32,}={0,2}')
        matches = secret_pattern.findall(input_text)
        for match in matches:
            if len(match) >= 32:
                logging.log_security_event("potential_secret_exposure", user_id,
                                         "long secret-like string detected", "high")
                raise errors.new_security_error("Potential secret exposure detected", None)

    def _validate_urls(self, input_text: str, user_id: str) -> None:
        """Validate any URLs found in the input."""
        # Find potential URLs
        url_pattern = re.compile(r'https?://[^\s]+')
        urls = url_pattern.findall(input_text)

        for url_str in urls:
            try:
                parsed_url = urlparse(url_str)
                self._validate_url(parsed_url, user_id)
            except Exception:
                logging.log_security_event("malformed_url", user_id,
                                         f"malformed URL detected: {url_str}", "medium")
                raise errors.new_validation_error("Invalid URL format")

    def _validate_url(self, parsed_url, user_id: str) -> None:
        """Validate a single URL for security issues."""
        # Block dangerous schemes
        suspicious_schemes = ["file", "ftp", "data", "javascript"]
        if parsed_url.scheme.lower() in suspicious_schemes:
            logging.log_security_event("dangerous_url_scheme", user_id,
                                     f"dangerous URL scheme: {parsed_url.scheme}", "high")
            raise errors.new_security_error("Dangerous URL scheme detected", None)

        # Block private/internal IPs
        if self._is_private_ip(parsed_url.hostname or ""):
            logging.log_security_event("private_ip_access", user_id,
                                     f"attempt to access private IP: {parsed_url.hostname}", "high")
            raise errors.new_security_error("Access to private networks blocked", None)

        # Check for URL shorteners that could hide malicious links
        suspicious_domains = [
            "bit.ly", "tinyurl.com", "t.co", "goo.gl", "ow.ly",
            "discord.gg",  # Discord invites can be spam
        ]

        hostname_lower = (parsed_url.hostname or "").lower()
        for domain in suspicious_domains:
            if domain in hostname_lower:
                logging.log_security_event("suspicious_domain", user_id,
                                         f"suspicious domain detected: {parsed_url.hostname}", "medium")
                # Don't block, just log for monitoring
                break

    def _is_private_ip(self, hostname: str) -> bool:
        """Check if an IP address is in a private range."""
        private_patterns = [
            "localhost",
            "127.",
            "192.168.",
            "10.",
            "172.16.", "172.17.", "172.18.", "172.19.",
            "172.20.", "172.21.", "172.22.", "172.23.",
            "172.24.", "172.25.", "172.26.", "172.27.",
            "172.28.", "172.29.", "172.30.", "172.31.",
            "0.0.0.0",
            "::1",
            "fe80:",
        ]

        hostname_lower = hostname.lower()
        return any(hostname_lower.startswith(pattern) for pattern in private_patterns)


class RateLimiter:
    """Simple rate limiting functionality."""

    def __init__(self, limit: int, window_seconds: int):
        self.requests: dict[str, list[float]] = {}
        self.limit = limit
        self.window = window_seconds

    def allow(self, user_id: str) -> bool:
        """Check if a request should be allowed."""
        now = time.time()

        # Clean old requests
        if user_id in self.requests:
            self.requests[user_id] = [
                timestamp for timestamp in self.requests[user_id]
                if now - timestamp <= self.window
            ]
        else:
            self.requests[user_id] = []

        # Check if under limit
        if len(self.requests[user_id]) >= self.limit:
            return False

        # Add current request
        self.requests[user_id].append(now)
        return True


class TokenValidator:
    """Secure token validation and generation."""

    def __init__(self):
        self.valid_tokens: dict[str, float] = {}  # token -> expiry timestamp

    def generate_secure_token(self) -> str:
        """Generate a cryptographically secure token."""
        token = secrets.token_hex(32)
        expiry = time.time() + 900  # 15 minutes
        self.valid_tokens[token] = expiry
        return token

    def validate_token(self, token: str) -> bool:
        """Validate a token securely."""
        if token not in self.valid_tokens:
            return False

        if time.time() > self.valid_tokens[token]:
            del self.valid_tokens[token]
            return False

        return True

    def invalidate_token(self, token: str) -> None:
        """Securely invalidate a token."""
        self.valid_tokens.pop(token, None)

    def cleanup_expired_tokens(self) -> None:
        """Clean up expired tokens."""
        now = time.time()
        expired_tokens = [
            token for token, expiry in self.valid_tokens.items()
            if now > expiry
        ]
        for token in expired_tokens:
            del self.valid_tokens[token]


def secure_compare(a: str, b: str) -> bool:
    """Perform constant-time string comparison."""
    if len(a) != len(b):
        return False

    result = 0
    for x, y in zip(a.encode(), b.encode(), strict=False):
        result |= x ^ y

    return result == 0


def sanitize_input(input_text: str) -> str:
    """Sanitize input for safe display."""
    # Use html.escape for proper HTML escaping
    return html.escape(input_text, quote=True)


def validate_discord_id(discord_id: str) -> None:
    """Validate Discord snowflake IDs."""
    if not discord_id.isdigit():
        raise errors.new_validation_error("Discord ID must be numeric")

    if not (17 <= len(discord_id) <= 19):
        raise errors.new_validation_error("Invalid Discord ID format")


def check_permissions(user_id: str, required_permissions: list[str]) -> None:
    """Validate user permissions for sensitive operations."""
    # This would integrate with Discord permissions or a custom permission system
    # For now, implement basic admin check

    admin_users = {
        # These would come from configuration
        "123456789012345678",  # Example admin ID
    }

    if user_id in admin_users:
        return  # Admin has all permissions

    # For non-admins, would check specific permissions
    # This is a placeholder implementation
    raise errors.new_permission_error("Insufficient permissions", None)


def log_security_incident(incident: str, user_id: str, details: str, severity: str = "medium") -> None:
    """Log a security incident with appropriate severity."""
    logging.log_security_event(incident, user_id, details, severity)

    # For critical incidents, could trigger additional alerting
    if severity == "critical":
        logger = logging.with_component("security")
        logger.error(
            "CRITICAL SECURITY INCIDENT",
            incident=incident,
            user_id=user_id,
            details=details,
        )


# Global instances
default_input_validator = InputValidator()
default_token_validator = TokenValidator()


def validate_user_input(input_text: str, user_id: str, max_length: int = 2000) -> None:
    """Validate user input using the default validator."""
    validator = InputValidator(max_length)
    validator.validate_input(input_text, user_id)


def generate_token() -> str:
    """Generate a secure token using the default validator."""
    return default_token_validator.generate_secure_token()


def validate_token(token: str) -> bool:
    """Validate a token using the default validator."""
    return default_token_validator.validate_token(token)
