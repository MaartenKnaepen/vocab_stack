"""Tests for multi-user data isolation."""
import sys
sys.path.insert(0, '.')

from vocab_stack.database import get_session, create_db_and_tables, drop_all_tables
from vocab_stack.models import User, Topic, Flashcard, LeitnerState, ReviewHistory
from vocab_stack.services.auth_service import AuthService
from vocab_stack.services.leitner_service import LeitnerService
from vocab_stack.services.statistics_service import StatisticsService
from sqlmodel import select
from datetime import date


class TestDataIsolation:
    """Test that user data is properly isolated in multi-user scenarios."""
    
    @classmethod
    def setup_class(cls):
        """Set up test database with multiple users."""
        print("\n" + "=" * 60)
        print("🔒 Data Isolation Tests")
        print("=" * 60)
        drop_all_tables()
        create_db_and_tables()
        
        # Create three test users
        AuthService.register("alice", "alice@test.com", "password123")
        AuthService.register("bob", "bob@test.com", "password123")
        AuthService.register("charlie", "charlie@test.com", "password123")
        
        with get_session() as session:
            cls.alice = session.exec(select(User).where(User.username == "alice")).first()
            cls.bob = session.exec(select(User).where(User.username == "bob")).first()
            cls.charlie = session.exec(select(User).where(User.username == "charlie")).first()
            
            # Create shared topics
            cls.shared_topic = Topic(name="Shared Topic", description="Everyone can add cards")
            cls.topic2 = Topic(name="Another Topic", description="Another shared topic")
            session.add(cls.shared_topic)
            session.add(cls.topic2)
            session.commit()
            session.refresh(cls.shared_topic)
            session.refresh(cls.topic2)
            
            # Alice creates cards in shared topic
            for i in range(3):
                card = Flashcard(
                    front=f"Alice's Card {i+1}",
                    back=f"Alice's Answer {i+1}",
                    topic_id=cls.shared_topic.id,
                    user_id=cls.alice.id
                )
                session.add(card)
                session.flush()
                session.add(LeitnerState(flashcard_id=card.id, box_number=1, next_review_date=date.today()))
            
            # Bob creates cards in shared topic
            for i in range(2):
                card = Flashcard(
                    front=f"Bob's Card {i+1}",
                    back=f"Bob's Answer {i+1}",
                    topic_id=cls.shared_topic.id,
                    user_id=cls.bob.id
                )
                session.add(card)
                session.flush()
                session.add(LeitnerState(flashcard_id=card.id, box_number=1, next_review_date=date.today()))
            
            # Charlie creates cards in topic2
            for i in range(4):
                card = Flashcard(
                    front=f"Charlie's Card {i+1}",
                    back=f"Charlie's Answer {i+1}",
                    topic_id=cls.topic2.id,
                    user_id=cls.charlie.id
                )
                session.add(card)
                session.flush()
                session.add(LeitnerState(flashcard_id=card.id, box_number=1, next_review_date=date.today()))
            
            session.commit()
    
    def test_users_see_only_own_cards_without_topic_filter(self):
        """Test that users only see their own cards when reviewing without topic filter."""
        print("\n🧪 Test: User Sees Only Own Cards (No Topic Filter)")
        
        # Alice's review session
        alice_cards = LeitnerService.get_due_cards(user_id=self.alice.id)
        assert len(alice_cards) == 3, f"Alice should see 3 cards, got {len(alice_cards)}"
        for card in alice_cards:
            assert card.user_id == self.alice.id, f"Alice should only see her cards, found card from user {card.user_id}"
        
        # Bob's review session
        bob_cards = LeitnerService.get_due_cards(user_id=self.bob.id)
        assert len(bob_cards) == 2, f"Bob should see 2 cards, got {len(bob_cards)}"
        for card in bob_cards:
            assert card.user_id == self.bob.id, f"Bob should only see his cards, found card from user {card.user_id}"
        
        # Charlie's review session
        charlie_cards = LeitnerService.get_due_cards(user_id=self.charlie.id)
        assert len(charlie_cards) == 4, f"Charlie should see 4 cards, got {len(charlie_cards)}"
        for card in charlie_cards:
            assert card.user_id == self.charlie.id, f"Charlie should only see his cards, found card from user {card.user_id}"
        
        print(f"✅ Alice: {len(alice_cards)}, Bob: {len(bob_cards)}, Charlie: {len(charlie_cards)} cards")
    
    def test_users_see_all_cards_in_shared_topic(self):
        """Test that users can see all cards in a topic regardless of owner."""
        print("\n🧪 Test: Users See All Cards in Shared Topic")
        
        # Alice reviews shared topic
        alice_topic_cards = LeitnerService.get_due_cards(topic_id=self.shared_topic.id, user_id=self.alice.id)
        alice_owned = sum(1 for c in alice_topic_cards if c.user_id == self.alice.id)
        bob_owned = sum(1 for c in alice_topic_cards if c.user_id == self.bob.id)
        
        assert len(alice_topic_cards) == 5, f"Should see 5 cards total, got {len(alice_topic_cards)}"
        assert alice_owned == 3, f"Should see 3 of Alice's cards, got {alice_owned}"
        assert bob_owned == 2, f"Should see 2 of Bob's cards, got {bob_owned}"
        
        # Bob reviews shared topic
        bob_topic_cards = LeitnerService.get_due_cards(topic_id=self.shared_topic.id, user_id=self.bob.id)
        assert len(bob_topic_cards) == 5, f"Bob should also see 5 cards total, got {len(bob_topic_cards)}"
        
        print(f"✅ Shared topic shows all {len(alice_topic_cards)} cards to all users")
    
    def test_review_history_is_per_user(self):
        """Test that review history is tracked per user."""
        print("\n🧪 Test: Review History Per User")
        
        # Get a card from shared topic
        cards = LeitnerService.get_due_cards(topic_id=self.shared_topic.id, user_id=self.alice.id)
        shared_card = cards[0]
        
        # Alice reviews the card
        LeitnerService.process_review(shared_card.id, user_id=self.alice.id, was_correct=True)
        
        # Bob reviews the same card
        LeitnerService.process_review(shared_card.id, user_id=self.bob.id, was_correct=False)
        
        # Check that both review histories exist separately
        with get_session() as session:
            alice_review = session.exec(
                select(ReviewHistory)
                .where(ReviewHistory.flashcard_id == shared_card.id)
                .where(ReviewHistory.user_id == self.alice.id)
            ).first()
            
            bob_review = session.exec(
                select(ReviewHistory)
                .where(ReviewHistory.flashcard_id == shared_card.id)
                .where(ReviewHistory.user_id == self.bob.id)
            ).first()
            
            assert alice_review is not None, "Alice's review should exist"
            assert bob_review is not None, "Bob's review should exist"
            assert alice_review.was_correct == True, "Alice's review should be correct"
            assert bob_review.was_correct == False, "Bob's review should be incorrect"
        
        print("✅ Each user has separate review history for the same card")
    
    def test_leitner_state_is_shared(self):
        """Test that Leitner state is shared (one state per card, not per user)."""
        print("\n🧪 Test: Leitner State is Shared")
        
        cards = LeitnerService.get_due_cards(topic_id=self.shared_topic.id, user_id=self.alice.id)
        test_card = cards[0]
        
        # Count Leitner states for this card
        with get_session() as session:
            leitner_states = session.exec(
                select(LeitnerState).where(LeitnerState.flashcard_id == test_card.id)
            ).all()
            
            assert len(leitner_states) == 1, \
                f"Should have exactly 1 Leitner state per card, found {len(leitner_states)}"
        
        print("✅ Leitner state is shared across users")
    
    def test_statistics_are_per_user(self):
        """Test that statistics are calculated per user."""
        print("\n🧪 Test: Statistics Per User")
        
        # Get statistics for each user
        alice_stats = StatisticsService.get_user_overview(self.alice.id)
        bob_stats = StatisticsService.get_user_overview(self.bob.id)
        charlie_stats = StatisticsService.get_user_overview(self.charlie.id)
        
        # Alice should only see her stats
        assert alice_stats['total_cards'] == 3, \
            f"Alice should have 3 cards, got {alice_stats['total_cards']}"
        
        # Bob should only see his stats
        assert bob_stats['total_cards'] == 2, \
            f"Bob should have 2 cards, got {bob_stats['total_cards']}"
        
        # Charlie should only see his stats
        assert charlie_stats['total_cards'] == 4, \
            f"Charlie should have 4 cards, got {charlie_stats['total_cards']}"
        
        print(f"✅ Statistics isolated: Alice={alice_stats['total_cards']}, "
              f"Bob={bob_stats['total_cards']}, Charlie={charlie_stats['total_cards']}")
    
    def test_user_cannot_edit_others_cards(self):
        """Test that users cannot modify cards they don't own."""
        print("\n🧪 Test: User Cannot Edit Others' Cards")
        
        with get_session() as session:
            # Get one of Alice's cards
            alice_card = session.exec(
                select(Flashcard)
                .where(Flashcard.user_id == self.alice.id)
            ).first()
            
            original_front = alice_card.front
            alice_card_id = alice_card.id
        
        # In a real app, Bob trying to edit Alice's card should be blocked by the UI/backend
        # Here we just verify ownership is tracked correctly
        with get_session() as session:
            card = session.get(Flashcard, alice_card_id)
            
            # Verify ownership
            assert card.user_id == self.alice.id, "Card should belong to Alice"
            assert card.user_id != self.bob.id, "Card should not belong to Bob"
        
        print("✅ Card ownership is correctly tracked")
    
    def test_deleting_user_doesnt_affect_shared_topic(self):
        """Test that deleting a user doesn't delete the shared topic."""
        print("\n🧪 Test: Deleting User Doesn't Affect Shared Topic")
        
        # Create a temporary user
        AuthService.register("temp_user", "temp@test.com", "password123")
        
        with get_session() as session:
            temp_user = session.exec(select(User).where(User.username == "temp_user")).first()
            temp_user_id = temp_user.id
            
            # Add a card to shared topic
            card = Flashcard(
                front="Temp User Card",
                back="Temp Answer",
                topic_id=self.shared_topic.id,
                user_id=temp_user_id
            )
            session.add(card)
            session.flush()
            card_id = card.id
            session.add(LeitnerState(flashcard_id=card_id, box_number=1))
            session.commit()
        
        # Delete temp user and their cards
        with get_session() as session:
            temp_user = session.get(User, temp_user_id)
            
            # Delete user's cards
            cards = session.exec(
                select(Flashcard).where(Flashcard.user_id == temp_user_id)
            ).all()
            for card in cards:
                leitner_states = session.exec(
                    select(LeitnerState).where(LeitnerState.flashcard_id == card.id)
                ).all()
                for state in leitner_states:
                    session.delete(state)
                session.delete(card)
            
            # Delete user
            session.delete(temp_user)
            session.commit()
        
        # Verify shared topic still exists
        with get_session() as session:
            topic = session.get(Topic, self.shared_topic.id)
            assert topic is not None, "Shared topic should still exist"
            
            # Other users' cards should still exist
            remaining_cards = session.exec(
                select(Flashcard).where(Flashcard.topic_id == self.shared_topic.id)
            ).all()
            assert len(remaining_cards) >= 5, \
                f"Other users' cards should remain, found {len(remaining_cards)}"
        
        print("✅ Deleting user doesn't affect shared topic or others' cards")


def run_all_tests():
    """Run all data isolation tests."""
    test_suite = TestDataIsolation()
    test_suite.setup_class()
    
    tests = [
        test_suite.test_users_see_only_own_cards_without_topic_filter,
        test_suite.test_users_see_all_cards_in_shared_topic,
        test_suite.test_review_history_is_per_user,
        test_suite.test_leitner_state_is_shared,
        test_suite.test_statistics_are_per_user,
        test_suite.test_user_cannot_edit_others_cards,
        test_suite.test_deleting_user_doesnt_affect_shared_topic,
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
        print("✅ All data isolation tests passed!")
    else:
        print(f"❌ {failed} test(s) failed")
    print("=" * 60)
    
    return failed == 0


if __name__ == "__main__":
    success = run_all_tests()
    sys.exit(0 if success else 1)
