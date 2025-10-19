"""Comprehensive tests for Leitner algorithm."""
import sys
sys.path.insert(0, '.')

from datetime import date, timedelta
from vocab_stack.database import get_session, create_db_and_tables, drop_all_tables
from vocab_stack.models import User, Topic, Flashcard, LeitnerState
from vocab_stack.services.leitner_service import LeitnerService
from vocab_stack.utils.date_helpers import (
    calculate_next_review_date,
    get_review_interval,
    is_due_for_review
)


def setup_test_data():
    """Create test data for Leitner tests."""
    # Clean slate
    drop_all_tables()
    create_db_and_tables()
    
    with get_session() as session:
        # Create user
        user = User(username="test_leitner", email="leitner@test.com")
        session.add(user)
        session.flush()
        
        # Create topic
        topic = Topic(name="Leitner Test Topic")
        session.add(topic)
        session.flush()
        
        # Create flashcards
        cards = []
        for i in range(5):
            card = Flashcard(
                front=f"Test Card {i+1}",
                back=f"Answer {i+1}",
                topic_id=topic.id,
                user_id=user.id
            )
            session.add(card)
            session.flush()
            
            # Create Leitner state (all start in Box 1)
            leitner = LeitnerState(
                flashcard_id=card.id,
                box_number=1,
                next_review_date=date.today()
            )
            session.add(leitner)
            cards.append(card)
        
        session.commit()
        return user.id, topic.id, [c.id for c in cards]


def test_date_calculations():
    """Test date helper functions."""
    print("\n🧪 Testing Date Calculations...")
    
    # Test review intervals
    assert get_review_interval(1) == 1, "Box 1 should be 1 day"
    assert get_review_interval(2) == 3, "Box 2 should be 3 days"
    assert get_review_interval(3) == 7, "Box 3 should be 7 days"
    assert get_review_interval(4) == 14, "Box 4 should be 14 days"
    assert get_review_interval(5) == 30, "Box 5 should be 30 days"
    
    # Test next review date calculation
    base_date = date(2024, 1, 1)
    assert calculate_next_review_date(1, base_date) == date(2024, 1, 2)
    assert calculate_next_review_date(3, base_date) == date(2024, 1, 8)
    assert calculate_next_review_date(5, base_date) == date(2024, 1, 31)
    
    # Test due for review
    assert is_due_for_review(date.today()) == True
    assert is_due_for_review(date.today() - timedelta(days=1)) == True
    assert is_due_for_review(date.today() + timedelta(days=1)) == False
    
    print("✅ Date calculations working correctly")


def test_card_progression_correct():
    """Test card moves from Box 1→2→3→4→5 on correct answers."""
    print("\n🧪 Testing Card Progression (Correct Answers)...")
    
    user_id, topic_id, card_ids = setup_test_data()
    card_id = card_ids[0]
    
    # Test progression through all boxes
    expected_boxes = [2, 3, 4, 5, 5]  # Box 5 stays at 5
    
    for i, expected_box in enumerate(expected_boxes):
        result = LeitnerService.process_review(
            flashcard_id=card_id,
            user_id=user_id,
            was_correct=True
        )
        
        assert result["new_box"] == expected_box, \
            f"After review {i+1}, expected box {expected_box}, got {result['new_box']}"
        
        print(f"   Review {i+1}: Box {result['old_box']} → Box {result['new_box']} ✓")
    
    # Verify final state
    stats = LeitnerService.get_card_statistics(card_id)
    assert stats["box_number"] == 5, "Card should be in Box 5"
    assert stats["correct_count"] == 5, "Should have 5 correct reviews"
    assert stats["incorrect_count"] == 0, "Should have 0 incorrect reviews"
    
    print("✅ Card progression working correctly")


def test_card_regression_incorrect():
    """Test card moves back to Box 1 on incorrect answer."""
    print("\n🧪 Testing Card Regression (Incorrect Answer)...")
    
    user_id, topic_id, card_ids = setup_test_data()
    card_id = card_ids[1]
    
    # Move card to Box 3
    for _ in range(2):
        LeitnerService.process_review(card_id, user_id, was_correct=True)
    
    stats = LeitnerService.get_card_statistics(card_id)
    assert stats["box_number"] == 3, "Card should be in Box 3"
    
    # Answer incorrectly
    result = LeitnerService.process_review(
        flashcard_id=card_id,
        user_id=user_id,
        was_correct=False
    )
    
    assert result["old_box"] == 3, "Should have been in Box 3"
    assert result["new_box"] == 1, "Should move back to Box 1"
    assert result["moved_down"] == True, "Should indicate moved down"
    
    stats = LeitnerService.get_card_statistics(card_id)
    assert stats["box_number"] == 1, "Card should be in Box 1"
    assert stats["incorrect_count"] == 1, "Should have 1 incorrect review"
    
    print("✅ Card regression working correctly")


def test_box5_stays_on_correct():
    """Test that Box 5 stays in Box 5 on correct answer."""
    print("\n🧪 Testing Box 5 Stays on Correct...")
    
    user_id, topic_id, card_ids = setup_test_data()
    card_id = card_ids[2]
    
    # Move card to Box 5
    for _ in range(4):
        LeitnerService.process_review(card_id, user_id, was_correct=True)
    
    stats = LeitnerService.get_card_statistics(card_id)
    assert stats["box_number"] == 5, "Card should be in Box 5"
    
    # Answer correctly again (should stay in Box 5)
    result = LeitnerService.process_review(card_id, user_id, was_correct=True)
    
    assert result["new_box"] == 5, "Should stay in Box 5"
    
    stats = LeitnerService.get_card_statistics(card_id)
    assert stats["box_number"] == 5, "Card should still be in Box 5"
    
    print("✅ Box 5 stays on correct working correctly")


def test_next_review_dates():
    """Test next review dates calculated correctly for each box."""
    print("\n🧪 Testing Next Review Date Calculation...")
    
    user_id, topic_id, card_ids = setup_test_data()
    card_id = card_ids[3]
    
    # After correct answer, card moves to next box
    # Box 1 → Box 2 (next review in 3 days)
    # Box 2 → Box 3 (next review in 7 days)
    # Box 3 → Box 4 (next review in 14 days)
    # Box 4 → Box 5 (next review in 30 days)
    # Box 5 → Box 5 (next review in 30 days)
    expected_intervals = [3, 7, 14, 30, 30]  # Days for boxes 2-5
    
    for i, expected_days in enumerate(expected_intervals, start=1):
        result = LeitnerService.process_review(card_id, user_id, was_correct=True)
        
        # Calculate expected next review date based on NEW box
        expected_date = date.today() + timedelta(days=expected_days)
        actual_date = result["next_review_date"]
        
        assert actual_date == expected_date, \
            f"Box {result['new_box']}: Expected next review {expected_date}, got {actual_date}"
        
        print(f"   Box {result['new_box']}: Next review in {expected_days} days ✓")
    
    print("✅ Next review dates calculated correctly")


def test_get_due_cards():
    """Test getting cards due for review today."""
    print("\n🧪 Testing Get Due Cards...")
    
    user_id, topic_id, card_ids = setup_test_data()
    
    # All cards should be due (all in Box 1 with today's date)
    due_cards = LeitnerService.get_due_cards(topic_id=topic_id, user_id=user_id)
    assert len(due_cards) == 5, f"Expected 5 due cards, got {len(due_cards)}"
    
    # Review one card (moves to Box 2, due in 3 days)
    LeitnerService.process_review(card_ids[0], user_id, was_correct=True)
    
    # Should now have 4 due cards
    due_cards = LeitnerService.get_due_cards(topic_id=topic_id, user_id=user_id)
    assert len(due_cards) == 4, f"Expected 4 due cards, got {len(due_cards)}"
    
    print("✅ Get due cards working correctly")


def test_topic_progress():
    """Test topic progress statistics."""
    print("\n🧪 Testing Topic Progress...")
    
    user_id, topic_id, card_ids = setup_test_data()
    
    # Initial state: all cards in Box 1
    progress = LeitnerService.get_topic_progress(topic_id, user_id)
    assert progress["total"] == 5, "Should have 5 total cards"
    assert progress["by_box"][1] == 5, "All should be in Box 1"
    assert progress["mastered"] == 0, "None mastered"
    
    # Move 2 cards to Box 5 (mastered)
    for _ in range(4):
        LeitnerService.process_review(card_ids[0], user_id, was_correct=True)
        LeitnerService.process_review(card_ids[1], user_id, was_correct=True)
    
    progress = LeitnerService.get_topic_progress(topic_id, user_id)
    assert progress["mastered"] == 2, "Should have 2 mastered cards"
    assert progress["mastered_percentage"] == 40.0, "Should be 40% mastered"
    
    print("✅ Topic progress tracking working correctly")


def test_review_history():
    """Test review history is recorded."""
    print("\n🧪 Testing Review History...")
    
    user_id, topic_id, card_ids = setup_test_data()
    card_id = card_ids[4]
    
    # Perform several reviews
    LeitnerService.process_review(card_id, user_id, was_correct=True, time_spent_seconds=10)
    LeitnerService.process_review(card_id, user_id, was_correct=False, time_spent_seconds=15)
    LeitnerService.process_review(card_id, user_id, was_correct=True, time_spent_seconds=8)
    
    # Check statistics
    stats = LeitnerService.get_card_statistics(card_id)
    assert stats["total_reviews"] == 3, "Should have 3 total reviews"
    assert stats["correct_count"] == 2, "Should have 2 correct"
    assert stats["incorrect_count"] == 1, "Should have 1 incorrect"
    assert stats["accuracy"] == 66.67, "Should be 66.67% accurate"
    
    print("✅ Review history recorded correctly")


def run_all_leitner_tests():
    """Run all Leitner algorithm tests."""
    print("=" * 70)
    print("🚀 Running Leitner Algorithm Tests")
    print("=" * 70)
    
    test_date_calculations()
    test_card_progression_correct()
    test_card_regression_incorrect()
    test_box5_stays_on_correct()
    test_next_review_dates()
    test_get_due_cards()
    test_topic_progress()
    test_review_history()
    
    print("\n" + "=" * 70)
    print("✅ All Leitner Algorithm Tests Passed!")
    print("=" * 70)


if __name__ == "__main__":
    run_all_leitner_tests()
