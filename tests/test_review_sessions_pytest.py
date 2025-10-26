"""Integration tests for review sessions - pytest version."""
import pytest
from vocab_stack.database import get_session, create_db_and_tables, drop_all_tables
from vocab_stack.models import User, Topic, Flashcard, LeitnerState, ReviewHistory
from vocab_stack.services.leitner_service import LeitnerService
from vocab_stack.services.auth_service import AuthService
from sqlmodel import select
from datetime import date, timedelta


@pytest.fixture(scope="module")
def setup_review_data():
    """Set up test database with users and cards."""
    drop_all_tables()
    create_db_and_tables()
    
    # Create test users
    _, _, user1 = AuthService.register_user("user1", "user1@test.com", "password123")
    _, _, user2 = AuthService.register_user("user2", "user2@test.com", "password123")
    
    with get_session() as session:
        # Create topics
        topic1 = Topic(name="Spanish Basics", description="Basic Spanish words")
        topic2 = Topic(name="French Basics", description="Basic French words")
        session.add(topic1)
        session.add(topic2)
        session.commit()
        session.refresh(topic1)
        session.refresh(topic2)
        
        # Create flashcards for user1 in topic1
        for i in range(5):
            card = Flashcard(
                front=f"Spanish Word {i+1}",
                back=f"Spanish Translation {i+1}",
                topic_id=topic1.id,
                user_id=user1.id
            )
            session.add(card)
            session.flush()
            
            # Create Leitner state (all due today)
            leitner = LeitnerState(
                flashcard_id=card.id,
                box_number=1,
                next_review_date=date.today()
            )
            session.add(leitner)
        
        # Create flashcards for user2 in topic1 (shared topic)
        for i in range(3):
            card = Flashcard(
                front=f"User2 Spanish Word {i+1}",
                back=f"User2 Spanish Translation {i+1}",
                topic_id=topic1.id,
                user_id=user2.id
            )
            session.add(card)
            session.flush()
            
            leitner = LeitnerState(
                flashcard_id=card.id,
                box_number=1,
                next_review_date=date.today()
            )
            session.add(leitner)
        
        # Create flashcards for user1 in topic2
        for i in range(2):
            card = Flashcard(
                front=f"French Word {i+1}",
                back=f"French Translation {i+1}",
                topic_id=topic2.id,
                user_id=user1.id
            )
            session.add(card)
            session.flush()
            
            leitner = LeitnerState(
                flashcard_id=card.id,
                box_number=1,
                next_review_date=date.today()
            )
            session.add(leitner)
        
        # Create some cards NOT due today
        card_future = Flashcard(
            front="Future Card",
            back="Not Due Yet",
            topic_id=topic1.id,
            user_id=user1.id
        )
        session.add(card_future)
        session.flush()
        
        leitner_future = LeitnerState(
            flashcard_id=card_future.id,
            box_number=2,
            next_review_date=date.today() + timedelta(days=3)
        )
        session.add(leitner_future)
        
        session.commit()
        
        # Get IDs before session closes
        user1_id = user1.id
        user2_id = user2.id
        topic1_id = topic1.id
        topic2_id = topic2.id
    
    yield {
        'user1_id': user1_id,
        'user2_id': user2_id,
        'topic1_id': topic1_id,
        'topic2_id': topic2_id,
    }
    
    drop_all_tables()


class TestReviewSessions:
    """Test review session functionality."""
    
    def test_get_due_cards_all(self, setup_review_data):
        """Test getting all due cards for a user."""
        user1_id = setup_review_data['user1_id']
        
        cards = LeitnerService.get_due_cards(user_id=user1_id)
        
        # User1 has 5 cards in topic1 + 2 cards in topic2 = 7 cards due today
        assert len(cards) == 7, f"User1 should have 7 due cards, got {len(cards)}"
        
        # All cards should belong to user1
        for card in cards:
            assert card.user_id == user1_id, "All cards should belong to user1"
    
    def test_get_due_cards_by_topic(self, setup_review_data):
        """Test getting due cards filtered by topic."""
        user1_id = setup_review_data['user1_id']
        user2_id = setup_review_data['user2_id']
        topic1_id = setup_review_data['topic1_id']
        
        # Get cards for topic1 (should include BOTH user1 and user2's cards)
        cards = LeitnerService.get_due_cards(topic_id=topic1_id, user_id=user1_id)
        
        # Topic1 has 5 cards from user1 + 3 cards from user2 = 8 cards
        assert len(cards) == 8, f"Topic1 should have 8 due cards, got {len(cards)}"
        
        # Cards should be from topic1
        for card in cards:
            assert card.topic_id == topic1_id, "All cards should be from topic1"
        
        # Should include cards from both users
        user_ids = set(card.user_id for card in cards)
        assert user1_id in user_ids, "Should include user1's cards"
        assert user2_id in user_ids, "Should include user2's cards"
    
    def test_due_date_filtering(self, setup_review_data):
        """Test that only cards due today are returned."""
        user1_id = setup_review_data['user1_id']
        
        cards = LeitnerService.get_due_cards(user_id=user1_id)
        
        # Check that future card is NOT included
        future_cards = [c for c in cards if c.front == "Future Card"]
        assert len(future_cards) == 0, "Future cards should not be included"
        
        # All cards should be due today or earlier
        with get_session() as session:
            for card in cards:
                leitner = session.exec(
                    select(LeitnerState).where(LeitnerState.flashcard_id == card.id)
                ).first()
                assert leitner.next_review_date <= date.today(), \
                    f"Card '{card.front}' has future due date: {leitner.next_review_date}"
    
    def test_user_data_isolation(self, setup_review_data):
        """Test that users only see their own cards (when not filtering by topic)."""
        user1_id = setup_review_data['user1_id']
        user2_id = setup_review_data['user2_id']
        
        # User1's cards
        user1_cards = LeitnerService.get_due_cards(user_id=user1_id)
        for card in user1_cards:
            assert card.user_id == user1_id, \
                f"User1 should only see their own cards, found card from user {card.user_id}"
        
        # User2's cards
        user2_cards = LeitnerService.get_due_cards(user_id=user2_id)
        for card in user2_cards:
            assert card.user_id == user2_id, \
                f"User2 should only see their own cards, found card from user {card.user_id}"
    
    def test_shared_topic_review(self, setup_review_data):
        """Test that users can review all cards in a shared topic."""
        user1_id = setup_review_data['user1_id']
        user2_id = setup_review_data['user2_id']
        topic1_id = setup_review_data['topic1_id']
        
        # User1 reviews topic1 - should see cards from both users
        cards = LeitnerService.get_due_cards(topic_id=topic1_id, user_id=user1_id)
        
        user1_count = sum(1 for c in cards if c.user_id == user1_id)
        user2_count = sum(1 for c in cards if c.user_id == user2_id)
        
        assert user1_count == 5, f"Should see 5 cards from user1, got {user1_count}"
        assert user2_count == 3, f"Should see 3 cards from user2, got {user2_count}"
    
    def test_review_correct_answer(self, setup_review_data):
        """Test reviewing a card with correct answer."""
        user1_id = setup_review_data['user1_id']
        
        # Get a card
        cards = LeitnerService.get_due_cards(user_id=user1_id)
        card = cards[0]
        
        with get_session() as session:
            # Get initial state
            leitner_before = session.exec(
                select(LeitnerState).where(LeitnerState.flashcard_id == card.id)
            ).first()
            initial_box = leitner_before.box_number
        
        # Process review as correct
        LeitnerService.process_review(card.id, user_id=user1_id, was_correct=True)
        
        with get_session() as session:
            # Check updated state
            leitner_after = session.exec(
                select(LeitnerState).where(LeitnerState.flashcard_id == card.id)
            ).first()
            
            assert leitner_after.box_number == initial_box + 1, \
                f"Box should increase from {initial_box} to {initial_box + 1}"
    
    def test_review_incorrect_answer(self, setup_review_data):
        """Test reviewing a card with incorrect answer."""
        user1_id = setup_review_data['user1_id']
        
        # Get a card and move it to box 3 first
        cards = LeitnerService.get_due_cards(user_id=user1_id)
        card = cards[1]  # Use second card
        
        with get_session() as session:
            leitner = session.exec(
                select(LeitnerState).where(LeitnerState.flashcard_id == card.id)
            ).first()
            leitner.box_number = 3
            session.add(leitner)
            session.commit()
        
        # Process review as incorrect
        LeitnerService.process_review(card.id, user_id=user1_id, was_correct=False)
        
        with get_session() as session:
            leitner_after = session.exec(
                select(LeitnerState).where(LeitnerState.flashcard_id == card.id)
            ).first()
            
            assert leitner_after.box_number == 1, \
                f"Box should reset to 1, got {leitner_after.box_number}"
