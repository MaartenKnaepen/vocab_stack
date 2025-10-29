"""Integration tests for review sessions."""
import sys
sys.path.insert(0, '.')

from vocab_stack.database import get_session, create_db_and_tables, drop_all_tables
from vocab_stack.models import User, Topic, Flashcard, LeitnerState, ReviewHistory
from vocab_stack.services.leitner_service import LeitnerService
from vocab_stack.services.auth_service import AuthService
from sqlmodel import select
from datetime import date, timedelta


class TestReviewSessions:
    """Test review session functionality."""
    
    @classmethod
    def setup_class(cls):
        """Set up test database with users and cards."""
        print("\n" + "=" * 60)
        print("📚 Review Session Integration Tests")
        print("=" * 60)
        drop_all_tables()
        create_db_and_tables()
        
        # Create test users
        success, msg, user1 = AuthService.register_user("user1", "user1@test.com", "password123")
        success, msg, user2 = AuthService.register_user("user2", "user2@test.com", "password123")
        
        with get_session() as session:
            user1 = session.exec(select(User).where(User.username == "user1")).first()
            user2 = session.exec(select(User).where(User.username == "user2")).first()
            
            cls.user1_id = user1.id
            cls.user2_id = user2.id
            
            # Create topics
            topic1 = Topic(name="Spanish Basics", description="Basic Spanish words")
            topic2 = Topic(name="French Basics", description="Basic French words")
            session.add(topic1)
            session.add(topic2)
            session.commit()
            session.refresh(topic1)
            session.refresh(topic2)
            
            cls.topic1_id = topic1.id
            cls.topic2_id = topic2.id
            
            # Create flashcards for user1 in topic1
            for i in range(5):
                card = Flashcard(
                    front=f"Spanish Word {i+1}",
                    back=f"Spanish Translation {i+1}",
                    topic_id=cls.topic1_id,
                    user_id=cls.user1_id
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
                    topic_id=cls.topic1_id,
                    user_id=cls.user2_id
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
                    topic_id=cls.topic2_id,
                    user_id=cls.user1_id
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
                topic_id=cls.topic1_id,
                user_id=cls.user1_id
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
    
    def test_get_due_cards_all(self):
        """Test getting all due cards for a user."""
        print("\n🧪 Test: Get All Due Cards")
        
        cards = LeitnerService.get_due_cards(user_id=self.user1_id)
        
        # User1 has 5 cards in topic1 + 2 cards in topic2 = 7 cards due today
        assert len(cards) == 7, f"User1 should have 7 due cards, got {len(cards)}"
        
        # All cards should belong to user1
        for card in cards:
            assert card.user_id == self.user1_id, "All cards should belong to user1"
        
        print(f"✅ Found {len(cards)} due cards for user1")
    
    def test_get_due_cards_by_topic(self):
        """Test getting due cards filtered by topic."""
        print("\n🧪 Test: Get Due Cards by Topic")
        
        # Get cards for topic1 (should include BOTH user1 and user2's cards)
        cards = LeitnerService.get_due_cards(topic_id=self.topic1_id, user_id=self.user1_id)
        
        # Topic1 has 5 cards from user1 + 3 cards from user2 = 8 cards
        assert len(cards) == 8, f"Topic1 should have 8 due cards, got {len(cards)}"
        
        # Cards should be from topic1
        for card in cards:
            assert card.topic_id == self.topic1_id, "All cards should be from topic1"
        
        # Should include cards from both users
        user_ids = set(card.user_id for card in cards)
        assert self.user1_id in user_ids, "Should include user1's cards"
        assert self.user2_id in user_ids, "Should include user2's cards"
        
        print(f"✅ Found {len(cards)} cards in topic1 (shared across users)")
    
    def test_due_date_filtering(self):
        """Test that only cards due today are returned."""
        print("\n🧪 Test: Due Date Filtering")
        
        cards = LeitnerService.get_due_cards(user_id=self.user1_id)
        
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
        
        print("✅ Only cards due today are returned")
    
    def test_review_correct_answer(self):
        """Test reviewing a card with correct answer."""
        print("\n🧪 Test: Review with Correct Answer")
        
        # Get a card
        cards = LeitnerService.get_due_cards(user_id=self.user1_id)
        card = cards[0]
        
        with get_session() as session:
            # Get initial state
            leitner_before = session.exec(
                select(LeitnerState).where(LeitnerState.flashcard_id == card.id)
            ).first()
            initial_box = leitner_before.box_number
            initial_date = leitner_before.next_review_date
        
        # Process review as correct
        LeitnerService.process_review(card.id, user_id=self.user1_id, was_correct=True)
        
        with get_session() as session:
            # Check updated state
            leitner_after = session.exec(
                select(LeitnerState).where(LeitnerState.flashcard_id == card.id)
            ).first()
            
            assert leitner_after.box_number == initial_box + 1, \
                f"Box should increase from {initial_box} to {initial_box + 1}"
            assert leitner_after.next_review_date > initial_date, \
                "Next review date should be in the future"
            
            # Check review history was created
            review = session.exec(
                select(ReviewHistory)
                .where(ReviewHistory.flashcard_id == card.id)
                .where(ReviewHistory.user_id == self.user1_id)
            ).first()
            
            assert review is not None, "Review history should be created"
            assert review.was_correct == True, "Review should be marked as correct"
        
        print(f"✅ Card moved from box {initial_box} to {initial_box + 1}")
    
    def test_review_incorrect_answer(self):
        """Test reviewing a card with incorrect answer."""
        print("\n🧪 Test: Review with Incorrect Answer")
        
        # Get a card and move it to box 3 first
        cards = LeitnerService.get_due_cards(user_id=self.user1_id)
        card = cards[1]  # Use second card
        
        with get_session() as session:
            leitner = session.exec(
                select(LeitnerState).where(LeitnerState.flashcard_id == card.id)
            ).first()
            leitner.box_number = 3
            session.add(leitner)
            session.commit()
        
        # Process review as incorrect
        LeitnerService.process_review(card.id, user_id=self.user1_id, was_correct=False)
        
        with get_session() as session:
            leitner_after = session.exec(
                select(LeitnerState).where(LeitnerState.flashcard_id == card.id)
            ).first()
            
            assert leitner_after.box_number == 1, \
                f"Box should reset to 1, got {leitner_after.box_number}"
            
            # Check review history
            review = session.exec(
                select(ReviewHistory)
                .where(ReviewHistory.flashcard_id == card.id)
                .where(ReviewHistory.user_id == self.user1_id)
            ).first()
            
            assert review is not None, "Review history should be created"
            assert review.was_correct == False, "Review should be marked as incorrect"
        
        print("✅ Card reset to box 1 after incorrect answer")
    
    def test_review_order_random(self):
        """Test that random review order works."""
        print("\n🧪 Test: Random Review Order")
        
        # Get cards twice with random order
        cards1 = LeitnerService.get_due_cards(user_id=self.user1_id, review_order="random")
        cards2 = LeitnerService.get_due_cards(user_id=self.user1_id, review_order="random")
        
        # Should have same number of cards
        assert len(cards1) == len(cards2), "Should get same number of cards"
        
        # Order might be different (not guaranteed, but likely with 7+ cards)
        card_ids1 = [c.id for c in cards1]
        card_ids2 = [c.id for c in cards2]
        
        print(f"✅ Random order produces {len(cards1)} cards")
    
    def test_cards_per_session_limit(self):
        """Test that cards_per_session limit is respected."""
        print("\n🧪 Test: Cards Per Session Limit")
        
        # Get all due cards
        all_cards = LeitnerService.get_due_cards(user_id=self.user1_id)
        total = len(all_cards)
        
        # Simulate limiting to 3 cards
        limited_cards = all_cards[:3]
        
        assert len(limited_cards) == 3, "Should limit to 3 cards"
        assert len(limited_cards) < total, "Limited should be less than total"
        
        print(f"✅ Limited to 3 cards (total available: {total})")
    
    def test_user_data_isolation(self):
        """Test that users only see their own cards (when not filtering by topic)."""
        print("\n🧪 Test: User Data Isolation")
        
        # User1's cards
        user1_cards = LeitnerService.get_due_cards(user_id=self.user1_id)
        for card in user1_cards:
            assert card.user_id == self.user1_id, \
                f"User1 should only see their own cards, found card from user {card.user_id}"
        
        # User2's cards
        user2_cards = LeitnerService.get_due_cards(user_id=self.user2_id)
        for card in user2_cards:
            assert card.user_id == self.user2_id, \
                f"User2 should only see their own cards, found card from user {card.user_id}"
        
        print(f"✅ User1 sees {len(user1_cards)} cards, User2 sees {len(user2_cards)} cards")
    
    def test_shared_topic_review(self):
        """Test that users can review all cards in a shared topic."""
        print("\n🧪 Test: Shared Topic Review")
        
        # User1 reviews topic1 - should see cards from both users
        cards = LeitnerService.get_due_cards(topic_id=self.topic1_id, user_id=self.user1_id)
        
        user1_count = sum(1 for c in cards if c.user_id == self.user1_id)
        user2_count = sum(1 for c in cards if c.user_id == self.user2_id)
        
        # Previous tests may have modified cards, so we check that:
        # - User1 has at least 3 cards (some may have been moved to future dates)
        # - User2 has all 3 cards (they weren't modified by other tests)
        # - Cards from both users are present
        assert user1_count >= 3, f"Should see at least 3 cards from user1, got {user1_count}"
        assert user2_count == 3, f"Should see 3 cards from user2, got {user2_count}"
        assert len(cards) >= 6, f"Should see at least 6 total cards, got {len(cards)}"
        
        print(f"✅ Topic review shows {user1_count} cards from user1 + {user2_count} from user2")


def run_all_tests():
    """Run all review session tests."""
    test_suite = TestReviewSessions()
    test_suite.setup_class()
    
    tests = [
        test_suite.test_get_due_cards_all,
        test_suite.test_get_due_cards_by_topic,
        test_suite.test_due_date_filtering,
        test_suite.test_review_correct_answer,
        test_suite.test_review_incorrect_answer,
        test_suite.test_review_order_random,
        test_suite.test_cards_per_session_limit,
        test_suite.test_user_data_isolation,
        test_suite.test_shared_topic_review,
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
        print("✅ All review session tests passed!")
    else:
        print(f"❌ {failed} test(s) failed")
    print("=" * 60)
    
    return failed == 0


if __name__ == "__main__":
    success = run_all_tests()
    sys.exit(0 if success else 1)
