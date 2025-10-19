"""Database initialization and helper functions."""
from sqlmodel import SQLModel, create_engine, Session
from vocab_stack.models import User, Topic, Flashcard, LeitnerState, ReviewHistory
import reflex as rx

# Get database URL from config
DATABASE_URL = rx.config.get_config().db_url

# Create engine
engine = create_engine(DATABASE_URL, echo=True)  # echo=True for SQL logging


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
