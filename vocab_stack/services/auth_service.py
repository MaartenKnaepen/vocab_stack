"""Authentication service for user management."""
import secrets
from datetime import datetime, timedelta
from typing import Optional
import bcrypt
from vocab_stack.database import get_session
from vocab_stack.models import User
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
        token = secrets.token_urlsafe(32)
        expires = datetime.utcnow() + timedelta(days=30)
        
        with get_session() as session:
            user = session.get(User, user_id)
            if user:
                user.session_token = token
                user.token_expires = expires
                user.last_login = datetime.utcnow()
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
            
            if user and user.token_expires and user.token_expires > datetime.utcnow():
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
        # Validate inputs
        if not username or not username.strip():
            return False, "Username is required", None
        
        if not email or not email.strip():
            return False, "Email is required", None
        
        if not password or len(password) < 6:
            return False, "Password must be at least 6 characters", None
        
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
        Authenticate a user.
        
        Returns:
            (success: bool, message: str, user: Optional[User])
        """
        if not username or not password:
            return False, "Username and password are required", None
        
        with get_session() as session:
            user = session.exec(
                select(User).where(User.username == username)
            ).first()
            
            if not user:
                return False, "Invalid username or password", None
            
            if not user.password_hash:
                return False, "Account not properly configured", None
            
            if not AuthService.verify_password(password, user.password_hash):
                return False, "Invalid username or password", None
            
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
