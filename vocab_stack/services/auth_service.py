"""Authentication service for user management."""
import secrets
from datetime import datetime, timedelta, timezone
from typing import Optional
import bcrypt
from vocab_stack.database import get_session
from vocab_stack.models import User
from vocab_stack.security import (
    login_rate_limiter, 
    generate_secure_token, 
    validate_password_strength, 
    sanitize_input
)
from sqlmodel import select


class AuthService:
    """Service for authentication and session management."""
    
    @staticmethod
    def hash_password(password: str) -> str:
        """Hash a password using bcrypt."""
        salt = bcrypt.gensalt()
        hashed = bcrypt.hashpw(password.encode('utf-8'), salt)
        return hashed.decode('utf-8')
    
    @staticmethod
    def verify_password(password: str, password_hash: str) -> bool:
        """Verify a password against its hash."""
        try:
            return bcrypt.checkpw(password.encode('utf-8'), password_hash.encode('utf-8'))
        except Exception:
            return False
    
    @staticmethod
    def create_session_token(user_id: int) -> str:
        """Generate and store a session token for the user."""
        token = generate_secure_token(32)
        expires = datetime.now(timezone.utc) + timedelta(days=30)
        
        with get_session() as session:
            user = session.get(User, user_id)
            if user:
                user.session_token = token
                user.token_expires = expires
                user.last_login = datetime.now(timezone.utc)
                session.add(user)
                session.commit()
        
        return token
    
    @staticmethod
    def validate_token(token: str) -> Optional[User]:
        """Validate a session token and return the user if valid."""
        if not token:
            return None
        
        with get_session() as session:
            user = session.exec(
                select(User).where(User.session_token == token)
            ).first()
            
            if user and user.token_expires:
                # Ensure both datetimes are timezone-aware for comparison
                now = datetime.now(timezone.utc)
                expires = user.token_expires
                
                # If stored datetime is naive, make it aware (assume UTC)
                if expires.tzinfo is None:
                    expires = expires.replace(tzinfo=timezone.utc)
                
                if expires > now:
                    return user
        
        return None
    
    @staticmethod
    def logout(user_id: int):
        """Invalidate the user's session token."""
        with get_session() as session:
            user = session.get(User, user_id)
            if user:
                user.session_token = None
                user.token_expires = None
                session.add(user)
                session.commit()
    
    @staticmethod
    def register_user(username: str, email: str, password: str) -> tuple[bool, str, Optional[User]]:
        """
        Register a new user.
        
        Returns:
            (success: bool, message: str, user: Optional[User])
        """
        # Sanitize inputs
        username = sanitize_input(username, max_length=50)
        email = sanitize_input(email, max_length=255)
        
        # Validate inputs
        if not username:
            return False, "Username is required", None
        
        if not email:
            return False, "Email is required", None
        
        # Validate password strength
        is_valid, error_msg = validate_password_strength(password)
        if not is_valid:
            return False, error_msg, None
        
        with get_session() as session:
            # Check if username exists
            existing_user = session.exec(
                select(User).where(User.username == username)
            ).first()
            
            if existing_user:
                return False, "Username already taken", None
            
            # Check if email exists
            existing_email = session.exec(
                select(User).where(User.email == email)
            ).first()
            
            if existing_email:
                return False, "Email already registered", None
            
            # Create user
            password_hash = AuthService.hash_password(password)
            user = User(
                username=username,
                email=email,
                password_hash=password_hash
            )
            session.add(user)
            session.commit()
            session.refresh(user)
            
            return True, "Registration successful", user
    
    @staticmethod
    def login_user(username: str, password: str) -> tuple[bool, str, Optional[User]]:
        """
        Authenticate a user with rate limiting.
        
        Returns:
            (success: bool, message: str, user: Optional[User])
        """
        if not username or not password:
            return False, "Username and password are required", None
        
        # Check rate limiting
        is_locked, remaining_seconds = login_rate_limiter.is_locked_out(username)
        if is_locked:
            minutes = remaining_seconds // 60
            seconds = remaining_seconds % 60
            return False, f"Too many failed attempts. Try again in {minutes}m {seconds}s", None
        
        with get_session() as session:
            user = session.exec(
                select(User).where(User.username == username)
            ).first()
            
            if not user:
                # Record failed attempt
                login_rate_limiter.record_attempt(username, success=False)
                return False, "Invalid username or password", None
            
            if not user.password_hash:
                return False, "Account not properly configured", None
            
            if not AuthService.verify_password(password, user.password_hash):
                # Record failed attempt
                login_rate_limiter.record_attempt(username, success=False)
                return False, "Invalid username or password", None
            
            # Record successful attempt (clears rate limiting)
            login_rate_limiter.record_attempt(username, success=True)
            
            return True, "Login successful", user
    
    @staticmethod
    def is_admin(user_id: int) -> bool:
        """Check if a user is an admin."""
        with get_session() as session:
            user = session.get(User, user_id)
            return user.is_admin if user else False
    
    @staticmethod
    def promote_to_admin(user_id: int) -> bool:
        """Promote a user to admin."""
        with get_session() as session:
            user = session.get(User, user_id)
            if user:
                user.is_admin = True
                session.add(user)
                session.commit()
                return True
        return False
