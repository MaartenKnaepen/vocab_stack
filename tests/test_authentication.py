"""Comprehensive authentication and authorization tests."""
import pytest
from vocab_stack.database import get_session, create_db_and_tables, drop_all_tables
from vocab_stack.models import User
from vocab_stack.services.auth_service import AuthService
from sqlmodel import select


@pytest.fixture(scope="module")
def setup_database():
    """Set up test database."""
    drop_all_tables()
    create_db_and_tables()
    yield
    # Cleanup after all tests
    drop_all_tables()


class TestAuthentication:
    """Test authentication functionality."""
    
    def test_user_registration(self, setup_database):
        """Test user registration with valid data."""
        
        success, message, user = AuthService.register_user(
            username="testuser",
            email="test@example.com",
            password="password123"
        )
        
        assert success, f"Registration failed: {message}"
        assert user is not None, "User should be returned"
        assert user.id is not None, "User ID should be set"
        
        with get_session() as session:
            db_user = session.get(User, user.id)
            assert db_user is not None, "User should exist in database"
            assert db_user.username == "testuser"
            assert db_user.email == "test@example.com"
            assert db_user.password_hash != "password123", "Password should be hashed"

    
    def test_duplicate_username(self, setup_database):
        """Test registration with duplicate username."""
        
        success, message, user = AuthService.register_user(
            username="testuser",  # Already exists
            email="different@example.com",
            password="password123"
        )
        
        assert not success, "Should fail with duplicate username"
        assert "username" in message.lower(), "Error message should mention username"
        assert user is None, "No user should be returned"

    
    def test_duplicate_email(self, setup_database):
        """Test registration with duplicate email."""
        
        success, message, user = AuthService.register_user(
            username="differentuser",
            email="test@example.com",  # Already exists
            password="password123"
        )
        
        assert not success, "Should fail with duplicate email"
        assert "email" in message.lower(), "Error message should mention email"
        assert user is None, "No user should be returned"

    
    def test_password_hashing(self, setup_database):
        """Test that passwords are properly hashed."""
        
        password = "mysecretpassword"
        hashed = AuthService.hash_password(password)
        
        assert hashed != password, "Password should be hashed"
        assert len(hashed) > 20, "Hash should be reasonably long"
        assert AuthService.verify_password(password, hashed), "Should verify correct password"
        assert not AuthService.verify_password("wrongpassword", hashed), "Should reject wrong password"

    
    def test_successful_login(self, setup_database):
        """Test login with correct credentials."""
        
        success, message, user = AuthService.login_user(
            username="testuser",
            password="password123"
        )
        
        assert success, f"Login failed: {message}"
        assert user is not None, "User should be returned"
        assert user.id is not None, "Should have user_id"
        assert user.username == "testuser", "Should have username"

    
    def test_login_wrong_password(self, setup_database):
        """Test login with incorrect password."""
        
        success, message, user = AuthService.login_user(
            username="testuser",
            password="wrongpassword"
        )
        
        assert not success, "Should fail with wrong password"
        assert user is None, "No user should be returned"

    
    def test_login_nonexistent_user(self, setup_database):
        """Test login with non-existent username."""
        
        success, message, user = AuthService.login_user(
            username="nonexistent",
            password="password123"
        )
        
        assert not success, "Should fail with non-existent user"
        assert user is None, "No user should be returned"

    
    def test_session_token_validation(self, setup_database):
        """Test session token validation."""
        
        # Login to get a user
        success, message, user = AuthService.login_user(
            username="testuser",
            password="password123"
        )
        
        # Create a session token
        token = AuthService.create_session_token(user.id)
        
        # Validate the token
        validated_user = AuthService.validate_token(token)
        assert validated_user is not None, "Valid token should return user"
        assert validated_user.id == user.id, "Should return correct user"
        
        # Test invalid token
        invalid_user = AuthService.validate_token("invalid_token_xyz")
        assert invalid_user is None, "Invalid token should return None"

    
    def test_admin_flag(self, setup_database):
        """Test admin flag on users."""
        
        # Create regular user
        success, message, user = AuthService.register_user(
            username="regularuser",
            email="regular@example.com",
            password="password123"
        )
        
        assert user.is_admin == False, "New users should not be admin by default"
        
        # Make user admin
        result = AuthService.promote_to_admin(user.id)
        assert result == True, "Should successfully promote to admin"
        
        # Verify
        is_admin = AuthService.is_admin(user.id)
        assert is_admin == True, "User should now be admin"

    
    def test_logout(self, setup_database):
        """Test logout functionality."""
        
        # Login first
        success, message, user = AuthService.login_user(
            username="testuser",
            password="password123"
        )
        
        # Create session token
        token = AuthService.create_session_token(user.id)
        
        # Verify token works
        validated = AuthService.validate_token(token)
        assert validated is not None, "Token should be valid"
        
        # Logout
        AuthService.logout(user.id)
        
        # Token should no longer be valid
        validated_after = AuthService.validate_token(token)
        assert validated_after is None, "Token should be invalid after logout"
