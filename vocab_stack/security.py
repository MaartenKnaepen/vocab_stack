"""Security utilities for the application."""
from datetime import datetime, timedelta, timezone
from collections import defaultdict
from typing import Dict, Tuple
import secrets


class RateLimiter:
    """Simple in-memory rate limiter for login attempts."""
    
    def __init__(self):
        # Store: {identifier: [(timestamp, attempt_count)]}
        self._attempts: Dict[str, list] = defaultdict(list)
        self._lockouts: Dict[str, datetime] = {}
        
        # Configuration
        self.max_attempts = 5
        self.window_minutes = 15
        self.lockout_minutes = 30
    
    def is_locked_out(self, identifier: str) -> Tuple[bool, int]:
        """
        Check if an identifier is locked out.
        
        Returns:
            (is_locked, remaining_seconds)
        """
        if identifier in self._lockouts:
            lockout_until = self._lockouts[identifier]
            if datetime.now(timezone.utc) < lockout_until:
                remaining = (lockout_until - datetime.now(timezone.utc)).seconds
                return True, remaining
            else:
                # Lockout expired
                del self._lockouts[identifier]
                self._attempts[identifier] = []
        
        return False, 0
    
    def record_attempt(self, identifier: str, success: bool = False) -> Tuple[bool, int]:
        """
        Record a login attempt.
        
        Args:
            identifier: Username or IP address
            success: Whether the attempt was successful
            
        Returns:
            (is_allowed, attempts_remaining)
        """
        now = datetime.now(timezone.utc)
        window_start = now - timedelta(minutes=self.window_minutes)
        
        # Clean old attempts
        self._attempts[identifier] = [
            (timestamp, count) 
            for timestamp, count in self._attempts[identifier]
            if timestamp > window_start
        ]
        
        if success:
            # Clear attempts on successful login
            self._attempts[identifier] = []
            if identifier in self._lockouts:
                del self._lockouts[identifier]
            return True, self.max_attempts
        
        # Record failed attempt
        self._attempts[identifier].append((now, 1))
        
        # Count attempts in window
        attempt_count = len(self._attempts[identifier])
        
        if attempt_count >= self.max_attempts:
            # Lock out the identifier
            self._lockouts[identifier] = now + timedelta(minutes=self.lockout_minutes)
            return False, 0
        
        return True, self.max_attempts - attempt_count
    
    def clear(self, identifier: str):
        """Clear rate limiting for an identifier."""
        if identifier in self._attempts:
            del self._attempts[identifier]
        if identifier in self._lockouts:
            del self._lockouts[identifier]


# Global rate limiter instance
login_rate_limiter = RateLimiter()


def generate_secure_token(length: int = 32) -> str:
    """
    Generate a cryptographically secure random token.
    
    Args:
        length: Length of the token in bytes
        
    Returns:
        Hex string token
    """
    return secrets.token_hex(length)


def generate_csrf_token() -> str:
    """Generate a CSRF token for form protection."""
    return secrets.token_urlsafe(32)


class SecurityHeaders:
    """Security headers for HTTP responses."""
    
    @staticmethod
    def get_headers() -> dict:
        """
        Get recommended security headers.
        
        Returns:
            Dictionary of security headers
        """
        return {
            # Prevent clickjacking
            "X-Frame-Options": "DENY",
            
            # Prevent MIME type sniffing
            "X-Content-Type-Options": "nosniff",
            
            # XSS Protection
            "X-XSS-Protection": "1; mode=block",
            
            # Referrer Policy
            "Referrer-Policy": "strict-origin-when-cross-origin",
            
            # Content Security Policy (basic)
            "Content-Security-Policy": (
                "default-src 'self'; "
                "script-src 'self' 'unsafe-inline' 'unsafe-eval'; "
                "style-src 'self' 'unsafe-inline'; "
                "img-src 'self' data: https:; "
                "font-src 'self' data:; "
                "connect-src 'self';"
            ),
        }
    
    @staticmethod
    def get_cors_headers(allowed_origin: str = "*") -> dict:
        """
        Get CORS headers.
        
        Args:
            allowed_origin: Allowed origin(s) for CORS
            
        Returns:
            Dictionary of CORS headers
        """
        return {
            "Access-Control-Allow-Origin": allowed_origin,
            "Access-Control-Allow-Methods": "GET, POST, PUT, DELETE, OPTIONS",
            "Access-Control-Allow-Headers": "Content-Type, Authorization",
            "Access-Control-Max-Age": "3600",
        }


def validate_password_strength(password: str) -> Tuple[bool, str]:
    """
    Validate password strength.
    
    Args:
        password: Password to validate
        
    Returns:
        (is_valid, error_message)
    """
    if len(password) < 8:
        return False, "Password must be at least 8 characters long"
    
    if len(password) > 128:
        return False, "Password must be less than 128 characters"
    
    # Check for at least one letter and one number
    has_letter = any(c.isalpha() for c in password)
    has_number = any(c.isdigit() for c in password)
    
    if not (has_letter and has_number):
        return False, "Password must contain at least one letter and one number"
    
    return True, ""


def sanitize_input(text: str, max_length: int = 1000) -> str:
    """
    Sanitize user input to prevent injection attacks.
    
    Args:
        text: Input text to sanitize
        max_length: Maximum allowed length
        
    Returns:
        Sanitized text
    """
    if not text:
        return ""
    
    # Truncate to max length
    text = text[:max_length]
    
    # Remove any null bytes
    text = text.replace('\x00', '')
    
    # Strip leading/trailing whitespace
    text = text.strip()
    
    return text
