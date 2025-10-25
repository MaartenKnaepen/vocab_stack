"""Database models for vocabulary learning app."""
from typing import Optional, List
from datetime import datetime, date
from sqlmodel import Field, Relationship
import reflex as rx


class User(rx.Model, table=True):
    """User account information."""
    id: Optional[int] = Field(default=None, primary_key=True)
    username: str = Field(index=True, unique=True)
    email: str = Field(unique=True)
    password_hash: str  # Hashed password
    created_at: datetime = Field(default_factory=datetime.utcnow)
    
    # Session management
    session_token: Optional[str] = None
    token_expires: Optional[datetime] = None
    is_admin: bool = Field(default=False)
    last_login: Optional[datetime] = None
    
    # Preferences
    cards_per_session: int = Field(default=20, ge=5, le=100)
    review_order: str = Field(default="random")  # random, oldest_first, newest_first
    show_examples: bool = Field(default=True)
    theme: str = Field(default="light")  # light, dark
    daily_goal: int = Field(default=50, ge=10, le=200)
    answer_mode: str = Field(default="reveal")  # reveal, type
    
    # Relationships
    flashcards: List["Flashcard"] = Relationship(back_populates="user")


class Topic(rx.Model, table=True):
    """Vocabulary topic/category."""
    id: Optional[int] = Field(default=None, primary_key=True)
    name: str = Field(index=True, unique=True)
    description: Optional[str] = None
    created_at: datetime = Field(default_factory=datetime.utcnow)
    
    # Relationships
    flashcards: List["Flashcard"] = Relationship(back_populates="topic")


class Flashcard(rx.Model, table=True):
    """Individual vocabulary flashcard."""
    id: Optional[int] = Field(default=None, primary_key=True)
    front: str  # Question/word
    back: str   # Answer/definition
    example: Optional[str] = None
    created_at: datetime = Field(default_factory=datetime.utcnow)
    
    # Foreign Keys
    topic_id: int = Field(foreign_key="topic.id")
    user_id: int = Field(foreign_key="user.id")
    
    # Relationships
    topic: Topic = Relationship(back_populates="flashcards")
    user: User = Relationship(back_populates="flashcards")
    review_history: List["ReviewHistory"] = Relationship(back_populates="flashcard")
    leitner_state: Optional["LeitnerState"] = Relationship(back_populates="flashcard")


class LeitnerState(rx.Model, table=True):
    """Current Leitner box state for each flashcard."""
    id: Optional[int] = Field(default=None, primary_key=True)
    box_number: int = Field(default=1, ge=1, le=5)  # Boxes 1-5
    next_review_date: date = Field(default_factory=date.today)
    last_reviewed: Optional[datetime] = None
    correct_count: int = Field(default=0, ge=0)
    incorrect_count: int = Field(default=0, ge=0)
    
    # Foreign Key (One-to-One with Flashcard)
    flashcard_id: int = Field(foreign_key="flashcard.id", unique=True)
    
    # Relationship
    flashcard: Flashcard = Relationship(back_populates="leitner_state")


class ReviewHistory(rx.Model, table=True):
    """Historical record of each review session."""
    id: Optional[int] = Field(default=None, primary_key=True)
    review_date: datetime = Field(default_factory=datetime.utcnow)
    was_correct: bool
    time_spent_seconds: Optional[int] = Field(default=None, ge=0)
    
    # Foreign Keys
    flashcard_id: int = Field(foreign_key="flashcard.id")
    user_id: int = Field(foreign_key="user.id")
    
    # Relationships
    flashcard: Flashcard = Relationship(back_populates="review_history")
