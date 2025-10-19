# Phase 1: Project Setup & Data Models - Implementation Guide

## Overview
This guide provides detailed implementation instructions for Phase 1 of the Vocabulary Learning App, focusing on setting up the Reflex project structure and implementing all database models with SQLModel/SQLAlchemy.

**Estimated Time**: 3-4 hours  
**Goal**: Working database with all tables, can create/read records via Python shell

---

## Prerequisites

### Required Dependencies
```bash
pip install reflex sqlmodel
```

### Technology Stack
- **Reflex**: Full-stack Python web framework (uses SQLModel for ORM)
- **SQLModel**: Database ORM (combines SQLAlchemy + Pydantic)
- **SQLite**: Default database (can be configured for PostgreSQL/MySQL)

---

## Step 1: Initialize Reflex Project (15 minutes)

### 1.1 Create Project Structure
```bash
mkdir vocab_app
cd vocab_app
reflex init
```

This creates the following structure:
```
vocab_app/
├── .web/              # Frontend build files (auto-generated)
├── assets/            # Static assets (images, CSS, etc.)
├── vocab_app/         # Main application directory
│   └── __init__.py
├── rxconfig.py        # Reflex configuration
└── requirements.txt   # Python dependencies
```

### 1.2 Configure Database
In `rxconfig.py`, configure the database URL:

```python
import reflex as rx

config = rx.Config(
    app_name="vocab_app",
    # Database configuration
    db_url="sqlite:///reflex.db",  # Default SQLite
    # For PostgreSQL: "postgresql://user:password@localhost/vocab_db"
)
```

---

## Step 2: Define Database Models (60 minutes)

Create `vocab_app/models.py` with all 5 tables following the schema from the plan.

### 2.1 Import Required Libraries
```python
from typing import Optional, List
from datetime import datetime, date
from sqlmodel import Field, Relationship, SQLModel
import reflex as rx
```

### 2.2 User Model
```python
class User(rx.Model, table=True):
    """User account information."""
    id: Optional[int] = Field(default=None, primary_key=True)
    username: str = Field(index=True, unique=True)
    email: str = Field(unique=True)
    created_at: datetime = Field(default_factory=datetime.utcnow)
    
    # Relationships
    flashcards: List["Flashcard"] = Relationship(back_populates="user")
```

**Key Points:**
- `rx.Model` is Reflex's wrapper around SQLModel, providing `table=True` behavior
- `Field(default=None, primary_key=True)` creates auto-incrementing ID
- `index=True` creates database index for faster queries
- `unique=True` enforces unique constraint
- `default_factory` for dynamic defaults (like timestamps)

### 2.3 Topic Model
```python
class Topic(rx.Model, table=True):
    """Vocabulary topic/category."""
    id: Optional[int] = Field(default=None, primary_key=True)
    name: str = Field(index=True, unique=True)
    description: Optional[str] = None
    created_at: datetime = Field(default_factory=datetime.utcnow)
    
    # Relationships
    flashcards: List["Flashcard"] = Relationship(back_populates="topic")
```

### 2.4 Flashcard Model
```python
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
```

**Relationship Explanation:**
- `foreign_key="topic.id"` creates FK constraint to topic table
- `Relationship(back_populates="...")` enables bidirectional navigation
- One Topic → Many Flashcards (One-to-Many)
- One User → Many Flashcards (One-to-Many)
- One Flashcard → Many ReviewHistory (One-to-Many)
- One Flashcard → One LeitnerState (One-to-One)

### 2.5 LeitnerState Model
```python
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
```

**Validation Constraints:**
- `ge=1, le=5`: Box number must be between 1-5
- `ge=0`: Counts must be non-negative
- `unique=True` on `flashcard_id` enforces one-to-one relationship

### 2.6 ReviewHistory Model
```python
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
```

---

## Step 3: Create Database Initialization Script (30 minutes)

Create `vocab_app/database.py`:

```python
"""Database initialization and helper functions."""
from sqlmodel import SQLModel, create_engine, Session
from vocab_app.models import User, Topic, Flashcard, LeitnerState, ReviewHistory
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
```

---

## Step 4: Write Database Migration (20 minutes)

Reflex uses Alembic for migrations automatically. To generate migration:

```bash
# Initialize migration (first time only)
reflex db init

# Create migration after model changes
reflex db makemigrations --message "Create initial tables"

# Apply migrations
reflex db migrate
```

**Manual Alternative (for testing):**
Create `scripts/init_db.py`:

```python
"""Initialize database with all tables."""
import sys
sys.path.insert(0, '.')

from vocab_app.database import create_db_and_tables

if __name__ == "__main__":
    print("Creating database tables...")
    create_db_and_tables()
    print("Done!")
```

Run with:
```bash
python scripts/init_db.py
```

---

## Step 5: Seed Database with Default User (30 minutes)

Create `scripts/seed_data.py`:

```python
"""Seed database with initial data."""
import sys
sys.path.insert(0, '.')

from vocab_app.database import get_session, create_db_and_tables
from vocab_app.models import User, Topic, Flashcard, LeitnerState
from datetime import date


def seed_database():
    """Seed database with default user and sample data."""
    
    # Ensure tables exist
    create_db_and_tables()
    
    with get_session() as session:
        # Check if data already exists
        existing_user = session.query(User).first()
        if existing_user:
            print("⚠️  Database already seeded!")
            return
        
        # Create default user
        user = User(
            username="demo_user",
            email="demo@example.com"
        )
        session.add(user)
        session.flush()  # Get user.id before commit
        
        # Create sample topics
        topics = [
            Topic(name="Basic Vocabulary", description="Common everyday words"),
            Topic(name="Business English", description="Professional terminology"),
            Topic(name="Travel Phrases", description="Useful phrases for travelers"),
        ]
        session.add_all(topics)
        session.flush()
        
        # Create sample flashcards
        flashcards = [
            Flashcard(
                front="Hello",
                back="A greeting",
                example="Hello, how are you?",
                topic_id=topics[0].id,
                user_id=user.id
            ),
            Flashcard(
                front="Meeting",
                back="A gathering of people for discussion",
                example="We have a meeting at 2 PM.",
                topic_id=topics[1].id,
                user_id=user.id
            ),
        ]
        session.add_all(flashcards)
        session.flush()
        
        # Create Leitner states for flashcards
        for card in flashcards:
            leitner = LeitnerState(
                flashcard_id=card.id,
                box_number=1,
                next_review_date=date.today()
            )
            session.add(leitner)
        
        session.commit()
        print("✅ Database seeded successfully!")
        print(f"   - Created user: {user.username}")
        print(f"   - Created {len(topics)} topics")
        print(f"   - Created {len(flashcards)} flashcards")


if __name__ == "__main__":
    seed_database()
```

Run with:
```bash
python scripts/seed_data.py
```

---

## Step 6: Test Database CRUD Operations (45 minutes)

Create `tests/test_database.py`:

```python
"""Test database CRUD operations."""
import sys
sys.path.insert(0, '.')

from vocab_app.database import get_session, create_db_and_tables
from vocab_app.models import User, Topic, Flashcard, LeitnerState, ReviewHistory
from datetime import datetime, date
from sqlmodel import select


def test_create_user():
    """Test creating a user."""
    print("\n🧪 Testing User Creation...")
    
    with get_session() as session:
        user = User(username="test_user", email="test@test.com")
        session.add(user)
        session.commit()
        session.refresh(user)  # Reload from DB to get ID
        
        print(f"✅ Created user: {user.username} (ID: {user.id})")
        return user.id


def test_read_users():
    """Test reading all users."""
    print("\n🧪 Testing User Reading...")
    
    with get_session() as session:
        statement = select(User)
        users = session.exec(statement).all()
        
        print(f"✅ Found {len(users)} users:")
        for user in users:
            print(f"   - {user.username} ({user.email})")


def test_create_topic_and_flashcard():
    """Test creating topic with flashcards."""
    print("\n🧪 Testing Topic and Flashcard Creation...")
    
    with get_session() as session:
        # Get or create user
        user = session.exec(select(User).where(User.username == "test_user")).first()
        
        # Create topic
        topic = Topic(name="Test Topic", description="For testing")
        session.add(topic)
        session.flush()
        
        # Create flashcard
        card = Flashcard(
            front="Test Front",
            back="Test Back",
            topic_id=topic.id,
            user_id=user.id
        )
        session.add(card)
        session.flush()
        
        # Create Leitner state
        leitner = LeitnerState(
            flashcard_id=card.id,
            box_number=1,
            next_review_date=date.today()
        )
        session.add(leitner)
        
        session.commit()
        print(f"✅ Created topic '{topic.name}' with flashcard")


def test_relationships():
    """Test relationship navigation."""
    print("\n🧪 Testing Relationships...")
    
    with get_session() as session:
        # Get topic with flashcards
        topic = session.exec(
            select(Topic).where(Topic.name == "Test Topic")
        ).first()
        
        print(f"✅ Topic '{topic.name}' has {len(topic.flashcards)} flashcards:")
        for card in topic.flashcards:
            print(f"   - {card.front} → {card.back}")
            if card.leitner_state:
                print(f"     Box: {card.leitner_state.box_number}")


def test_update_flashcard():
    """Test updating a flashcard."""
    print("\n🧪 Testing Flashcard Update...")
    
    with get_session() as session:
        card = session.exec(
            select(Flashcard).where(Flashcard.front == "Test Front")
        ).first()
        
        card.back = "Updated Back"
        session.add(card)
        session.commit()
        
        print(f"✅ Updated flashcard: {card.front} → {card.back}")


def test_delete_flashcard():
    """Test deleting a flashcard."""
    print("\n🧪 Testing Flashcard Deletion...")
    
    with get_session() as session:
        card = session.exec(
            select(Flashcard).where(Flashcard.front == "Test Front")
        ).first()
        
        if card:
            session.delete(card)
            session.commit()
            print(f"✅ Deleted flashcard: {card.front}")


def run_all_tests():
    """Run all CRUD tests."""
    print("=" * 60)
    print("🚀 Running Database CRUD Tests")
    print("=" * 60)
    
    create_db_and_tables()
    
    test_create_user()
    test_read_users()
    test_create_topic_and_flashcard()
    test_relationships()
    test_update_flashcard()
    test_delete_flashcard()
    
    print("\n" + "=" * 60)
    print("✅ All tests completed!")
    print("=" * 60)


if __name__ == "__main__":
    run_all_tests()
```

Run with:
```bash
python tests/test_database.py
```

---

## Step 7: Verify in Python Shell (15 minutes)

Test interactively:

```python
# Start Python shell from project root
python

# Import and test
from vocab_app.database import get_session
from vocab_app.models import User, Topic, Flashcard
from sqlmodel import select

# Get session
session = get_session()

# Query users
users = session.exec(select(User)).all()
print(f"Users: {[u.username for u in users]}")

# Query topics
topics = session.exec(select(Topic)).all()
print(f"Topics: {[t.name for t in topics]}")

# Query flashcards with relationships
cards = session.exec(select(Flashcard)).all()
for card in cards:
    print(f"{card.front} (Topic: {card.topic.name}, Box: {card.leitner_state.box_number})")

# Close session
session.close()
```

---

## Common Issues & Solutions

### Issue 1: Import Errors
**Problem**: `ModuleNotFoundError: No module named 'vocab_app'`

**Solution**: Ensure you're running scripts from project root and added `sys.path.insert(0, '.')` to scripts.

### Issue 2: Database Locked (SQLite)
**Problem**: `sqlite3.OperationalError: database is locked`

**Solution**: Close all other connections/sessions before operations. Use `with get_session() as session:` pattern.

### Issue 3: Foreign Key Violations
**Problem**: `IntegrityError: FOREIGN KEY constraint failed`

**Solution**: Ensure referenced records exist before creating relationships. Use `session.flush()` to get IDs before referencing.

### Issue 4: Relationship Not Working
**Problem**: `AttributeError: 'Flashcard' object has no attribute 'topic'`

**Solution**: Ensure `back_populates` matches relationship attribute name exactly in both models.

---

## Verification Checklist

- [ ] Reflex project initialized
- [ ] Database configured in `rxconfig.py`
- [ ] All 5 models defined in `models.py`
- [ ] Database tables created successfully
- [ ] Migration files generated (optional)
- [ ] Seed script creates default user
- [ ] All CRUD tests pass
- [ ] Can query data via Python shell
- [ ] Relationships working correctly
- [ ] Foreign key constraints enforced

---

## Next Steps

After completing Phase 1, you should have:
1. ✅ Working database schema with all 5 tables
2. ✅ Sample data loaded (user, topics, flashcards)
3. ✅ Verified CRUD operations work
4. ✅ Confirmed relationships are properly configured

**Ready for Phase 2**: Leitner Algorithm Implementation

---

## Additional Resources

### Reflex Documentation
- Project Setup: https://reflex.dev/docs/getting-started/installation/
- Database Models: https://reflex.dev/docs/database/overview/

### SQLModel Documentation
- Relationships: https://sqlmodel.tiangolo.com/tutorial/relationship-attributes/
- Foreign Keys: https://sqlmodel.tiangolo.com/tutorial/connect/create-connected-tables/
- Many-to-Many: https://sqlmodel.tiangolo.com/tutorial/many-to-many/

### Key Concepts
- **rx.Model**: Reflex wrapper around SQLModel for database models
- **Field()**: Define column properties (primary key, foreign key, defaults, constraints)
- **Relationship()**: Define relationships between models (one-to-many, many-to-one, one-to-one)
- **back_populates**: Enable bidirectional relationship navigation
- **rx.session()**: Get database session for queries and transactions

---

## Quick Reference: Common Operations

### Create Record
```python
with rx.session() as session:
    user = User(username="john", email="john@example.com")
    session.add(user)
    session.commit()
```

### Read Records
```python
with rx.session() as session:
    users = session.exec(select(User)).all()
    user = session.exec(select(User).where(User.username == "john")).first()
```

### Update Record
```python
with rx.session() as session:
    user = session.exec(select(User).where(User.id == 1)).first()
    user.email = "newemail@example.com"
    session.add(user)
    session.commit()
```

### Delete Record
```python
with rx.session() as session:
    user = session.exec(select(User).where(User.id == 1)).first()
    session.delete(user)
    session.commit()
```

### Query with Relationships
```python
with rx.session() as session:
    topic = session.exec(select(Topic).where(Topic.id == 1)).first()
    # Access related flashcards
    for card in topic.flashcards:
        print(card.front)
```

---

**Phase 1 Complete!** 🎉

Your database foundation is now ready for implementing the Leitner spaced repetition algorithm in Phase 2.
