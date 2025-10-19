"""Test database CRUD operations."""
import sys
import os
sys.path.insert(0, '.')

from vocab_stack.database import get_session, create_db_and_tables, drop_all_tables
from vocab_stack.models import User, Topic, Flashcard, LeitnerState, ReviewHistory
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
            # Delete associated LeitnerState first (due to foreign key)
            if card.leitner_state:
                session.delete(card.leitner_state)
            
            # Delete any review history
            for review in card.review_history:
                session.delete(review)
            
            # Now delete the card
            session.delete(card)
            session.commit()
            print(f"✅ Deleted flashcard: {card.front}")


def run_all_tests():
    """Run all CRUD tests."""
    print("=" * 60)
    print("🚀 Running Database CRUD Tests")
    print("=" * 60)
    
    # Clean slate for testing
    print("Resetting test database...")
    drop_all_tables()
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
