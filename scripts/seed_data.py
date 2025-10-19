"""Seed database with initial data."""
import sys
sys.path.insert(0, '.')

from vocab_stack.database import get_session, create_db_and_tables
from vocab_stack.models import User, Topic, Flashcard, LeitnerState
from datetime import date
from sqlmodel import select


def seed_database():
    """Seed database with default user and sample data."""
    
    # Ensure tables exist
    create_db_and_tables()
    
    with get_session() as session:
        # Check if data already exists
        existing_user = session.exec(select(User)).first()
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
