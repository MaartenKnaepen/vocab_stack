"""Application configuration."""
import os
from typing import List


class Config:
    """Application configuration settings."""
    
    # Environment
    ENV = os.getenv("ENV", "development")
    DEBUG = os.getenv("DEBUG", "True").lower() == "true"
    
    # Security
    SECRET_KEY = os.getenv("SECRET_KEY", "change-this-in-production-very-important-secret")
    
    # Session
    SESSION_COOKIE_SECURE = os.getenv("SESSION_COOKIE_SECURE", "False").lower() == "true"
    SESSION_COOKIE_HTTPONLY = True
    SESSION_COOKIE_SAMESITE = "Lax"
    SESSION_LIFETIME_DAYS = int(os.getenv("SESSION_LIFETIME_DAYS", "30"))
    
    # CORS
    CORS_ENABLED = os.getenv("CORS_ENABLED", "True").lower() == "true"
    CORS_ORIGINS = os.getenv("CORS_ORIGINS", "*").split(",")
    
    # Rate Limiting
    RATE_LIMIT_ENABLED = os.getenv("RATE_LIMIT_ENABLED", "True").lower() == "true"
    LOGIN_MAX_ATTEMPTS = int(os.getenv("LOGIN_MAX_ATTEMPTS", "5"))
    LOGIN_WINDOW_MINUTES = int(os.getenv("LOGIN_WINDOW_MINUTES", "15"))
    LOGIN_LOCKOUT_MINUTES = int(os.getenv("LOGIN_LOCKOUT_MINUTES", "30"))
    
    # HTTPS
    FORCE_HTTPS = os.getenv("FORCE_HTTPS", "False").lower() == "true"
    
    # Database
    DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///vocab_stack.db")
    
    @classmethod
    def is_production(cls) -> bool:
        """Check if running in production."""
        return cls.ENV == "production"
    
    @classmethod
    def validate_production_config(cls) -> List[str]:
        """
        Validate production configuration.
        
        Returns:
            List of validation errors (empty if valid)
        """
        errors = []
        
        if cls.is_production():
            if cls.SECRET_KEY == "change-this-in-production-very-important-secret":
                errors.append("SECRET_KEY must be changed in production")
            
            if not cls.SESSION_COOKIE_SECURE:
                errors.append("SESSION_COOKIE_SECURE should be True in production (requires HTTPS)")
            
            if not cls.FORCE_HTTPS:
                errors.append("FORCE_HTTPS should be True in production")
            
            if "*" in cls.CORS_ORIGINS:
                errors.append("CORS_ORIGINS should not include '*' in production")
        
        return errors


class DevelopmentConfig(Config):
    """Development configuration."""
    ENV = "development"
    DEBUG = True
    SESSION_COOKIE_SECURE = False
    FORCE_HTTPS = False


class ProductionConfig(Config):
    """Production configuration."""
    ENV = "production"
    DEBUG = False
    SESSION_COOKIE_SECURE = True
    FORCE_HTTPS = True
    CORS_ORIGINS = []  # Must be explicitly set


# Select config based on environment
def get_config() -> Config:
    """Get configuration based on environment."""
    env = os.getenv("ENV", "development")
    
    if env == "production":
        return ProductionConfig()
    else:
        return DevelopmentConfig()


# Global config instance
config = get_config()
