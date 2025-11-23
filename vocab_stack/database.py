"""Database initialization and helper functions."""
from sqlmodel import SQLModel, create_engine, Session
import reflex as rx

# Get database URL from config
DATABASE_URL = rx.config.get_config().db_url

# Create engine with connection pool settings for cloud databases
engine = create_engine(
    DATABASE_URL,
    pool_pre_ping=True,  # Verify connections before using them
    pool_recycle=300,  # Recycle connections after 5 minutes
    pool_size=2,  # Maximum number of connections in the pool (reduced for free tier)
    max_overflow=3,  # Maximum overflow connections (reduced for free tier)
    connect_args={
        "connect_timeout": 10,  # Connection timeout in seconds
        "options": "-c statement_timeout=30000"  # Query timeout (30 seconds)
    } if DATABASE_URL and "postgresql" in DATABASE_URL else {}
)


def create_db_and_tables():
    """Create all database tables."""
    SQLModel.metadata.create_all(engine)
    print("✅ Database tables created successfully!")


def get_session():
    """Get database session."""
    return Session(engine)


def drop_all_tables():
    """Drop all tables (use with caution!)"""
    SQLModel.metadata.drop_all(engine)
    print("⚠️  All tables dropped!")
