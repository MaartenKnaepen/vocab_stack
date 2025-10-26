"""Tests for security features."""
import pytest
from vocab_stack.security import (
    RateLimiter, 
    validate_password_strength, 
    sanitize_input,
    generate_secure_token
)
from vocab_stack.services.auth_service import AuthService
from vocab_stack.database import get_session, create_db_and_tables, drop_all_tables


@pytest.fixture(scope="function")
def clean_database():
    """Provide a clean database for each test."""
    drop_all_tables()
    create_db_and_tables()
    yield


class TestRateLimiting:
    """Test rate limiting functionality."""
    
    def test_rate_limiter_allows_initial_attempts(self):
        """Test that initial attempts are allowed."""
        limiter = RateLimiter()
        limiter.max_attempts = 3
        
        # First attempt should be allowed
        allowed, remaining = limiter.record_attempt("testuser", success=False)
        assert allowed == True
        assert remaining == 2
        
        # Second attempt should be allowed
        allowed, remaining = limiter.record_attempt("testuser", success=False)
        assert allowed == True
        assert remaining == 1
    
    def test_rate_limiter_locks_after_max_attempts(self):
        """Test that user is locked out after max attempts."""
        limiter = RateLimiter()
        limiter.max_attempts = 3
        
        # Use up all attempts
        for i in range(3):
            limiter.record_attempt("testuser", success=False)
        
        # Should be locked out
        is_locked, remaining = limiter.is_locked_out("testuser")
        assert is_locked == True
        assert remaining > 0
    
    def test_rate_limiter_resets_on_success(self):
        """Test that successful login resets the counter."""
        limiter = RateLimiter()
        limiter.max_attempts = 3
        
        # Record failed attempts
        limiter.record_attempt("testuser", success=False)
        limiter.record_attempt("testuser", success=False)
        
        # Successful login should reset
        allowed, remaining = limiter.record_attempt("testuser", success=True)
        assert allowed == True
        assert remaining == 3
        
        # Verify not locked out
        is_locked, _ = limiter.is_locked_out("testuser")
        assert is_locked == False
    
    def test_rate_limiting_integration_with_auth(self, clean_database):
        """Test rate limiting integration with login."""
        # Register a user
        AuthService.register_user("ratelimit_test", "rate@test.com", "Password123")
        
        # Try wrong password multiple times
        for i in range(5):
            success, message, user = AuthService.login_user("ratelimit_test", "wrongpassword")
            assert success == False
        
        # 6th attempt should be rate limited
        success, message, user = AuthService.login_user("ratelimit_test", "wrongpassword")
        assert success == False
        assert "Too many failed attempts" in message


class TestPasswordValidation:
    """Test password strength validation."""
    
    def test_password_too_short(self):
        """Test that short passwords are rejected."""
        is_valid, msg = validate_password_strength("abc123")
        assert is_valid == False
        assert "8 characters" in msg
    
    def test_password_no_letter(self):
        """Test that passwords without letters are rejected."""
        is_valid, msg = validate_password_strength("12345678")
        assert is_valid == False
        assert "letter" in msg
    
    def test_password_no_number(self):
        """Test that passwords without numbers are rejected."""
        is_valid, msg = validate_password_strength("abcdefgh")
        assert is_valid == False
        assert "number" in msg
    
    def test_password_valid(self):
        """Test that valid passwords are accepted."""
        is_valid, msg = validate_password_strength("Password123")
        assert is_valid == True
        assert msg == ""
    
    def test_password_integration_with_registration(self, clean_database):
        """Test password validation in registration."""
        # Weak password should fail
        success, message, user = AuthService.register_user("weakpw", "weak@test.com", "abc")
        assert success == False
        assert "8 characters" in message
        
        # Password without number should fail
        success, message, user = AuthService.register_user("weakpw", "weak@test.com", "abcdefgh")
        assert success == False
        assert "number" in message
        
        # Strong password should succeed
        success, message, user = AuthService.register_user("strongpw", "strong@test.com", "StrongPass123")
        assert success == True


class TestInputSanitization:
    """Test input sanitization."""
    
    def test_sanitize_removes_null_bytes(self):
        """Test that null bytes are removed."""
        result = sanitize_input("test\x00user")
        assert "\x00" not in result
        assert result == "testuser"
    
    def test_sanitize_strips_whitespace(self):
        """Test that whitespace is stripped."""
        result = sanitize_input("  username  ")
        assert result == "username"
    
    def test_sanitize_enforces_max_length(self):
        """Test that max length is enforced."""
        long_text = "a" * 200
        result = sanitize_input(long_text, max_length=50)
        assert len(result) == 50
    
    def test_sanitize_empty_input(self):
        """Test that empty input is handled."""
        result = sanitize_input("")
        assert result == ""
        
        result = sanitize_input(None)
        assert result == ""


class TestSecureTokens:
    """Test secure token generation."""
    
    def test_generate_token_length(self):
        """Test that tokens have correct length."""
        token = generate_secure_token(32)
        # Hex encoding doubles the length
        assert len(token) == 64  # 32 bytes = 64 hex chars
    
    def test_generate_token_uniqueness(self):
        """Test that tokens are unique."""
        token1 = generate_secure_token(32)
        token2 = generate_secure_token(32)
        assert token1 != token2
    
    def test_generate_token_randomness(self):
        """Test that tokens are random (basic check)."""
        tokens = [generate_secure_token(32) for _ in range(10)]
        # All should be unique
        assert len(set(tokens)) == 10


class TestAuthServiceSecurity:
    """Test security features in AuthService."""
    
    def test_registration_sanitizes_input(self, clean_database):
        """Test that registration sanitizes inputs."""
        # Username with whitespace
        success, msg, user = AuthService.register_user(
            "  testuser  ", 
            "  test@example.com  ", 
            "Password123"
        )
        assert success == True
        assert user.username == "testuser"
        assert user.email == "test@example.com"
    
    def test_password_hashing(self, clean_database):
        """Test that passwords are properly hashed."""
        success, msg, user = AuthService.register_user(
            "hashtest",
            "hash@test.com",
            "Password123"
        )
        
        assert success == True
        # Password should be hashed (bcrypt hashes start with $2b$)
        assert user.password_hash.startswith("$2b$")
        assert user.password_hash != "Password123"
    
    def test_session_token_security(self, clean_database):
        """Test that session tokens are secure."""
        # Create user
        AuthService.register_user("tokentest", "token@test.com", "Password123")
        
        # Login
        success, msg, user = AuthService.login_user("tokentest", "Password123")
        assert success == True
        
        # Create session token
        token = AuthService.create_session_token(user.id)
        
        # Token should be long and random
        assert len(token) > 32
        
        # Should be able to validate
        validated_user = AuthService.validate_token(token)
        assert validated_user is not None
        assert validated_user.id == user.id
