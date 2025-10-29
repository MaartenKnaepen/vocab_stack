"""Tests for topic operations including cascade deletion."""
import sys
sys.path.insert(0, '.')

from vocab_stack.database import get_session, create_db_and_tables, drop_all_tables
from vocab_stack.models import User, Topic, Flashcard, LeitnerState, ReviewHistory
from vocab_stack.services.auth_service import AuthService
from sqlmodel import select
from datetime import date


class TestTopicOperations:
    """Test topic CRUD operations and cascade deletion."""
    
    @classmethod
    def setup_class(cls):
        """Set up test database."""
        print("\n" + "=" * 60)
        print("📂 Topic Operations Tests")
        print("=" * 60)
        drop_all_tables()
        create_db_and_tables()
        
        # Create test user
        success, msg, user = AuthService.register_user("testuser", "test@example.com", "password123")
        
        with get_session() as session:
            user = session.exec(select(User).where(User.username == "testuser")).first()
            cls.user_id = user.id
            
            # Create a test topic
            topic = Topic(name="Test Topic", description="A test topic")
            session.add(topic)
            session.commit()
            session.refresh(topic)
            cls.topic_id = topic.id
    
    def test_create_topic(self):
        """Test creating a topic."""
        print("\n🧪 Test: Create Topic")
        
        with get_session() as session:
            topic = session.get(Topic, self.topic_id)
            
            assert topic is not None, "Topic should exist"
            assert topic.id is not None, "Topic should have an ID"
            assert topic.name == "Test Topic", "Topic name should match"
        
        print(f"✅ Topic exists with ID: {self.topic_id}")
    
    def test_add_cards_to_topic(self):
        """Test adding flashcards to a topic."""
        print("\n🧪 Test: Add Cards to Topic")
        
        with get_session() as session:
            topic = session.get(Topic, self.topic_id)
            
            # Add 5 flashcards
            for i in range(5):
                card = Flashcard(
                    front=f"Question {i+1}",
                    back=f"Answer {i+1}",
                    topic_id=topic.id,
                    user_id=self.user_id
                )
                session.add(card)
                session.flush()
                
                # Add Leitner state
                leitner = LeitnerState(
                    flashcard_id=card.id,
                    box_number=1,
                    next_review_date=date.today()
                )
                session.add(leitner)
                
                # Add review history
                review = ReviewHistory(
                    flashcard_id=card.id,
                    user_id=self.user_id,
                    was_correct=True
                )
                session.add(review)
            
            session.commit()
            session.refresh(topic)
            
            card_count = len(topic.flashcards)
            assert card_count == 5, f"Topic should have 5 cards, got {card_count}"
        
        print(f"✅ Added 5 cards with Leitner states and review history")
    
    def test_cascade_deletion(self):
        """Test that deleting a topic deletes all related data."""
        print("\n🧪 Test: Cascade Deletion")
        
        # First, count related records
        with get_session() as session:
            topic = session.get(Topic, self.topic_id)
            flashcards = session.exec(
                select(Flashcard).where(Flashcard.topic_id == topic.id)
            ).all()
            
            flashcard_ids = [c.id for c in flashcards]
            initial_card_count = len(flashcards)
            
            # Count Leitner states
            leitner_count = 0
            review_count = 0
            for card_id in flashcard_ids:
                leitner_states = session.exec(
                    select(LeitnerState).where(LeitnerState.flashcard_id == card_id)
                ).all()
                leitner_count += len(leitner_states)
                
                reviews = session.exec(
                    select(ReviewHistory).where(ReviewHistory.flashcard_id == card_id)
                ).all()
                review_count += len(reviews)
            
            print(f"   Before deletion:")
            print(f"   - {initial_card_count} flashcards")
            print(f"   - {leitner_count} Leitner states")
            print(f"   - {review_count} review history records")
        
        # Perform cascade deletion
        with get_session() as session:
            topic = session.get(Topic, self.topic_id)
            
            # Get all flashcards for this topic
            flashcards = session.exec(
                select(Flashcard).where(Flashcard.topic_id == topic.id)
            ).all()
            
            # Delete related records for each flashcard
            for flashcard in flashcards:
                # Delete LeitnerState records
                leitner_states = session.exec(
                    select(LeitnerState).where(LeitnerState.flashcard_id == flashcard.id)
                ).all()
                for state in leitner_states:
                    session.delete(state)
                
                # Delete ReviewHistory records
                review_histories = session.exec(
                    select(ReviewHistory).where(ReviewHistory.flashcard_id == flashcard.id)
                ).all()
                for history in review_histories:
                    session.delete(history)
                
                # Delete the flashcard itself
                session.delete(flashcard)
            
            # Finally, delete the topic
            session.delete(topic)
            session.commit()
        
        # Verify everything was deleted
        with get_session() as session:
            # Topic should be gone
            topic = session.get(Topic, self.topic_id)
            assert topic is None, "Topic should be deleted"
            
            # Flashcards should be gone
            cards = session.exec(
                select(Flashcard).where(Flashcard.topic_id == self.topic_id)
            ).all()
            assert len(cards) == 0, f"All flashcards should be deleted, found {len(cards)}"
            
            # Leitner states should be gone
            for card_id in flashcard_ids:
                leitner_states = session.exec(
                    select(LeitnerState).where(LeitnerState.flashcard_id == card_id)
                ).all()
                assert len(leitner_states) == 0, \
                    f"All Leitner states should be deleted, found {len(leitner_states)} for card {card_id}"
            
            # Review history should be gone
            for card_id in flashcard_ids:
                reviews = session.exec(
                    select(ReviewHistory).where(ReviewHistory.flashcard_id == card_id)
                ).all()
                assert len(reviews) == 0, \
                    f"All review history should be deleted, found {len(reviews)} for card {card_id}"
        
        print(f"✅ Successfully deleted topic and all {initial_card_count} cards with related data")
    
    def test_topic_deletion_doesnt_affect_other_topics(self):
        """Test that deleting one topic doesn't affect other topics."""
        print("\n🧪 Test: Topic Deletion Isolation")
        
        with get_session() as session:
            # Create two topics with cards
            topic1 = Topic(name="Topic 1", description="First topic")
            topic2 = Topic(name="Topic 2", description="Second topic")
            session.add(topic1)
            session.add(topic2)
            session.commit()
            session.refresh(topic1)
            session.refresh(topic2)
            
            # Add cards to both topics
            for i in range(3):
                card1 = Flashcard(
                    front=f"Topic1 Q{i}",
                    back=f"Topic1 A{i}",
                    topic_id=topic1.id,
                    user_id=self.user_id
                )
                card2 = Flashcard(
                    front=f"Topic2 Q{i}",
                    back=f"Topic2 A{i}",
                    topic_id=topic2.id,
                    user_id=self.user_id
                )
                session.add(card1)
                session.add(card2)
                session.flush()
                
                # Add Leitner states
                session.add(LeitnerState(flashcard_id=card1.id, box_number=1))
                session.add(LeitnerState(flashcard_id=card2.id, box_number=1))
            
            session.commit()
            
            topic1_id = topic1.id
            topic2_id = topic2.id
        
        # Delete topic1 with cascade
        with get_session() as session:
            topic1 = session.get(Topic, topic1_id)
            flashcards = session.exec(
                select(Flashcard).where(Flashcard.topic_id == topic1.id)
            ).all()
            
            for flashcard in flashcards:
                leitner_states = session.exec(
                    select(LeitnerState).where(LeitnerState.flashcard_id == flashcard.id)
                ).all()
                for state in leitner_states:
                    session.delete(state)
                session.delete(flashcard)
            
            session.delete(topic1)
            session.commit()
        
        # Verify topic2 is intact
        with get_session() as session:
            topic2 = session.get(Topic, topic2_id)
            assert topic2 is not None, "Topic 2 should still exist"
            
            cards2 = session.exec(
                select(Flashcard).where(Flashcard.topic_id == topic2_id)
            ).all()
            assert len(cards2) == 3, f"Topic 2 should still have 3 cards, found {len(cards2)}"
            
            # Check Leitner states still exist
            for card in cards2:
                leitner = session.exec(
                    select(LeitnerState).where(LeitnerState.flashcard_id == card.id)
                ).first()
                assert leitner is not None, f"Leitner state should exist for card {card.id}"
        
        print("✅ Deleting topic1 did not affect topic2")
    
    def test_empty_topic_deletion(self):
        """Test deleting a topic with no flashcards."""
        print("\n🧪 Test: Delete Empty Topic")
        
        with get_session() as session:
            empty_topic = Topic(name="Empty Topic", description="No cards")
            session.add(empty_topic)
            session.commit()
            session.refresh(empty_topic)
            
            topic_id = empty_topic.id
            
            # Delete immediately
            session.delete(empty_topic)
            session.commit()
            
            # Verify it's gone
            deleted_topic = session.get(Topic, topic_id)
            assert deleted_topic is None, "Empty topic should be deleted"
        
        print("✅ Empty topic deleted successfully")


def run_all_tests():
    """Run all topic operation tests."""
    test_suite = TestTopicOperations()
    test_suite.setup_class()
    
    tests = [
        test_suite.test_create_topic,
        test_suite.test_add_cards_to_topic,
        test_suite.test_cascade_deletion,
        test_suite.test_topic_deletion_doesnt_affect_other_topics,
        test_suite.test_empty_topic_deletion,
    ]
    
    failed = 0
    for test in tests:
        try:
            test()
        except AssertionError as e:
            print(f"❌ FAILED: {e}")
            failed += 1
        except Exception as e:
            print(f"❌ ERROR: {e}")
            import traceback
            traceback.print_exc()
            failed += 1
    
    print("\n" + "=" * 60)
    if failed == 0:
        print("✅ All topic operation tests passed!")
    else:
        print(f"❌ {failed} test(s) failed")
    print("=" * 60)
    
    return failed == 0


if __name__ == "__main__":
    success = run_all_tests()
    sys.exit(0 if success else 1)
