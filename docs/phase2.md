# Phase 2: Leitner Algorithm Implementation - Implementation Guide

## Overview
This guide provides detailed implementation instructions for Phase 2, focusing on the core spaced repetition logic using the Leitner system.

**Estimated Time**: 4-5 hours  
**Goal**: Fully tested Leitner system passing all test cases

---

## Prerequisites

- ✅ Phase 1 completed (database models working)
- ✅ All 5 tables created and seeded
- ✅ Understanding of Leitner spaced repetition concept

---

## Leitner System Overview

### Box System Rules
- **5 Boxes** numbered 1-5
- Cards start in **Box 1**
- **Correct answer** → Move to next box (Box 1→2, 2→3, etc.)
- **Incorrect answer** → Move back to Box 1
- **Box 5** → Stays in Box 5 on correct (mastered)

### Review Intervals
- **Box 1**: Review daily (every 1 day)
- **Box 2**: Review every 3 days
- **Box 3**: Review every 7 days
- **Box 4**: Review every 14 days
- **Box 5**: Review every 30 days

---

## Step 1: Create Date Helper Module (30 minutes)

Create `vocab_app/utils/date_helpers.py`:

```python
"""Date calculation utilities for Leitner algorithm."""
from datetime import date, timedelta


# Box review intervals (in days)
BOX_INTERVALS = {
    1: 1,   # Daily
    2: 3,   # Every 3 days
    3: 7,   # Weekly
    4: 14,  # Bi-weekly
    5: 30,  # Monthly
}


def get_review_interval(box_number: int) -> int:
    """
    Get review interval in days for a given box number.
    
    Args:
        box_number: Box number (1-5)
        
    Returns:
        Number of days until next review
        
    Raises:
        ValueError: If box_number is not between 1-5
    """
    if box_number not in BOX_INTERVALS:
        raise ValueError(f"Box number must be between 1-5, got {box_number}")
    
    return BOX_INTERVALS[box_number]


def calculate_next_review_date(box_number: int, last_reviewed: date = None) -> date:
    """
    Calculate next review date based on box number.
    
    Args:
        box_number: Current box number (1-5)
        last_reviewed: Date of last review (defaults to today)
        
    Returns:
        Date of next scheduled review
        
    Examples:
        >>> calculate_next_review_date(1, date(2024, 1, 1))
        date(2024, 1, 2)  # 1 day later
        
        >>> calculate_next_review_date(3, date(2024, 1, 1))
        date(2024, 1, 8)  # 7 days later
    """
    if last_reviewed is None:
        last_reviewed = date.today()
    
    interval_days = get_review_interval(box_number)
    next_date = last_reviewed + timedelta(days=interval_days)
    
    return next_date


def is_due_for_review(next_review_date: date) -> bool:
    """
    Check if a card is due for review today.
    
    Args:
        next_review_date: Scheduled review date
        
    Returns:
        True if review is due (today or overdue), False otherwise
    """
    return next_review_date <= date.today()


def days_until_review(next_review_date: date) -> int:
    """
    Calculate days until next review.
    
    Args:
        next_review_date: Scheduled review date
        
    Returns:
        Number of days (negative if overdue)
    """
    return (next_review_date - date.today()).days
```

---

## Step 2: Implement Leitner Service (90 minutes)

Create `vocab_app/services/leitner_service.py`:

```python
"""Leitner spaced repetition algorithm implementation."""
from datetime import datetime, date
from typing import List, Optional
from sqlmodel import select, and_

from vocab_app.models import Flashcard, LeitnerState, ReviewHistory, User
from vocab_app.utils.date_helpers import calculate_next_review_date, is_due_for_review
import reflex as rx


class LeitnerService:
    """Service for managing Leitner box algorithm."""
    
    @staticmethod
    def get_due_cards(topic_id: Optional[int] = None, user_id: Optional[int] = None) -> List[Flashcard]:
        """
        Get all flashcards due for review today.
        
        Args:
            topic_id: Filter by topic (optional)
            user_id: Filter by user (optional)
            
        Returns:
            List of flashcards due for review
            
        Example:
            >>> cards = LeitnerService.get_due_cards(topic_id=1, user_id=1)
            >>> print(f"Found {len(cards)} cards to review")
        """
        with rx.session() as session:
            # Build query
            query = select(Flashcard).join(LeitnerState)
            
            # Add filters
            conditions = [LeitnerState.next_review_date <= date.today()]
            
            if topic_id is not None:
                conditions.append(Flashcard.topic_id == topic_id)
            
            if user_id is not None:
                conditions.append(Flashcard.user_id == user_id)
            
            query = query.where(and_(*conditions))
            
            # Execute and return
            cards = session.exec(query).all()
            return cards
    
    @staticmethod
    def get_card_statistics(flashcard_id: int) -> dict:
        """
        Get statistics for a flashcard.
        
        Args:
            flashcard_id: ID of the flashcard
            
        Returns:
            Dictionary with statistics (box, correct_count, accuracy, etc.)
        """
        with rx.session() as session:
            leitner = session.exec(
                select(LeitnerState).where(LeitnerState.flashcard_id == flashcard_id)
            ).first()
            
            if not leitner:
                return {}
            
            total_reviews = leitner.correct_count + leitner.incorrect_count
            accuracy = (leitner.correct_count / total_reviews * 100) if total_reviews > 0 else 0
            
            return {
                "box_number": leitner.box_number,
                "correct_count": leitner.correct_count,
                "incorrect_count": leitner.incorrect_count,
                "total_reviews": total_reviews,
                "accuracy": round(accuracy, 2),
                "next_review_date": leitner.next_review_date,
                "last_reviewed": leitner.last_reviewed,
            }
    
    @staticmethod
    def process_review(
        flashcard_id: int,
        user_id: int,
        was_correct: bool,
        time_spent_seconds: Optional[int] = None
    ) -> dict:
        """
        Process a review and update Leitner state.
        
        Args:
            flashcard_id: ID of reviewed flashcard
            user_id: ID of user who reviewed
            was_correct: Whether answer was correct
            time_spent_seconds: Time spent on review (optional)
            
        Returns:
            Dictionary with updated state information
            
        Example:
            >>> result = LeitnerService.process_review(
            ...     flashcard_id=1,
            ...     user_id=1,
            ...     was_correct=True,
            ...     time_spent_seconds=15
            ... )
            >>> print(f"Card moved to box {result['new_box']}")
        """
        with rx.session() as session:
            # Get current Leitner state
            leitner = session.exec(
                select(LeitnerState).where(LeitnerState.flashcard_id == flashcard_id)
            ).first()
            
            if not leitner:
                raise ValueError(f"No Leitner state found for flashcard {flashcard_id}")
            
            # Store old state
            old_box = leitner.box_number
            
            # Update box number based on correctness
            if was_correct:
                leitner.correct_count += 1
                # Move to next box (max 5)
                leitner.box_number = min(leitner.box_number + 1, 5)
            else:
                leitner.incorrect_count += 1
                # Move back to box 1
                leitner.box_number = 1
            
            # Update review dates
            leitner.last_reviewed = datetime.utcnow()
            leitner.next_review_date = calculate_next_review_date(
                leitner.box_number,
                date.today()
            )
            
            # Save Leitner state
            session.add(leitner)
            
            # Create review history record
            review = ReviewHistory(
                flashcard_id=flashcard_id,
                user_id=user_id,
                was_correct=was_correct,
                time_spent_seconds=time_spent_seconds,
                review_date=datetime.utcnow()
            )
            session.add(review)
            
            session.commit()
            
            # Return summary
            return {
                "old_box": old_box,
                "new_box": leitner.box_number,
                "next_review_date": leitner.next_review_date,
                "correct_count": leitner.correct_count,
                "incorrect_count": leitner.incorrect_count,
                "moved_up": was_correct and old_box < 5,
                "moved_down": not was_correct,
            }
    
    @staticmethod
    def get_topic_progress(topic_id: int, user_id: int) -> dict:
        """
        Get learning progress for a topic.
        
        Args:
            topic_id: ID of the topic
            user_id: ID of the user
            
        Returns:
            Dictionary with progress statistics
        """
        with rx.session() as session:
            # Get all flashcards for topic/user
            cards = session.exec(
                select(Flashcard).where(
                    and_(
                        Flashcard.topic_id == topic_id,
                        Flashcard.user_id == user_id
                    )
                )
            ).all()
            
            if not cards:
                return {"total": 0, "by_box": {}}
            
            # Count cards by box
            box_counts = {1: 0, 2: 0, 3: 0, 4: 0, 5: 0}
            due_count = 0
            
            for card in cards:
                if card.leitner_state:
                    box_counts[card.leitner_state.box_number] += 1
                    if is_due_for_review(card.leitner_state.next_review_date):
                        due_count += 1
            
            mastered_count = box_counts[5]
            mastered_percentage = (mastered_count / len(cards) * 100) if cards else 0
            
            return {
                "total": len(cards),
                "by_box": box_counts,
                "due_today": due_count,
                "mastered": mastered_count,
                "mastered_percentage": round(mastered_percentage, 2),
            }
    
    @staticmethod
    def reset_card(flashcard_id: int) -> None:
        """
        Reset a card back to Box 1 (useful for re-learning).
        
        Args:
            flashcard_id: ID of the flashcard to reset
        """
        with rx.session() as session:
            leitner = session.exec(
                select(LeitnerState).where(LeitnerState.flashcard_id == flashcard_id)
            ).first()
            
            if leitner:
                leitner.box_number = 1
                leitner.next_review_date = date.today()
                leitner.last_reviewed = None
                session.add(leitner)
                session.commit()
```

---

## Step 3: Write Comprehensive Tests (90 minutes)

Create `tests/test_leitner_algorithm.py`:

```python
"""Comprehensive tests for Leitner algorithm."""
import sys
sys.path.insert(0, '.')

from datetime import date, timedelta
from vocab_app.database import get_session, create_db_and_tables
from vocab_app.models import User, Topic, Flashcard, LeitnerState
from vocab_app.services.leitner_service import LeitnerService
from vocab_app.utils.date_helpers import (
    calculate_next_review_date,
    get_review_interval,
    is_due_for_review
)


def setup_test_data():
    """Create test data for Leitner tests."""
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
    
    expected_intervals = [1, 3, 7, 14, 30]  # Days for boxes 1-5
    
    for i, expected_days in enumerate(expected_intervals, start=1):
        result = LeitnerService.process_review(card_id, user_id, was_correct=True)
        
        # Calculate expected next review date
        expected_date = date.today() + timedelta(days=expected_days)
        actual_date = result["next_review_date"]
        
        assert actual_date == expected_date, \
            f"Box {i}: Expected next review {expected_date}, got {actual_date}"
        
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
```

---

## Step 4: Run and Verify Tests (15 minutes)

```bash
# Run all tests
python tests/test_leitner_algorithm.py
```

Expected output:
```
======================================================================
🚀 Running Leitner Algorithm Tests
======================================================================

🧪 Testing Date Calculations...
✅ Date calculations working correctly

🧪 Testing Card Progression (Correct Answers)...
   Review 1: Box 1 → Box 2 ✓
   Review 2: Box 2 → Box 3 ✓
   Review 3: Box 3 → Box 4 ✓
   Review 4: Box 4 → Box 5 ✓
   Review 5: Box 5 → Box 5 ✓
✅ Card progression working correctly

... (all other tests)

======================================================================
✅ All Leitner Algorithm Tests Passed!
======================================================================
```

---

## Verification Checklist

- [ ] Date helper functions implemented
- [ ] Leitner service methods implemented
- [ ] Card moves Box 1→2 on correct
- [ ] Card moves Box 3→1 on incorrect
- [ ] Box 5 stays in Box 5 on correct
- [ ] Next review dates calculated correctly for each box
- [ ] Due cards query returns correct cards
- [ ] Topic progress tracking works
- [ ] Review history recorded properly
- [ ] All tests passing

---

## Common Edge Cases Handled

### 1. Box Boundaries
- ✅ Moving up from Box 5 stays at Box 5
- ✅ Moving down always goes to Box 1 (not box-1)

### 2. Date Handling
- ✅ Uses `date.today()` for consistency
- ✅ Handles overdue cards (past review dates)

### 3. Statistics
- ✅ Handles division by zero (0 reviews = 0% accuracy)
- ✅ Rounds percentages to 2 decimal places

---

## Integration Examples

### Example 1: Daily Review Session
```python
from vocab_app.services.leitner_service import LeitnerService

# Get cards due today for a user
due_cards = LeitnerService.get_due_cards(user_id=1)
print(f"You have {len(due_cards)} cards to review today!")

for card in due_cards:
    # Show card
    print(f"\nQuestion: {card.front}")
    user_answer = input("Your answer: ")
    print(f"Correct answer: {card.back}")
    
    # Get user feedback
    was_correct = input("Were you correct? (y/n): ").lower() == 'y'
    
    # Process review
    result = LeitnerService.process_review(
        flashcard_id=card.id,
        user_id=1,
        was_correct=was_correct
    )
    
    print(f"Box {result['old_box']} → Box {result['new_box']}")
    print(f"Next review: {result['next_review_date']}")
```

### Example 2: Topic Progress Dashboard
```python
from vocab_app.services.leitner_service import LeitnerService

# Get progress for a topic
progress = LeitnerService.get_topic_progress(topic_id=1, user_id=1)

print(f"Total cards: {progress['total']}")
print(f"Due today: {progress['due_today']}")
print(f"Mastered: {progress['mastered']} ({progress['mastered_percentage']}%)")
print("\nDistribution by box:")
for box, count in progress['by_box'].items():
    print(f"  Box {box}: {count} cards")
```

---

## Next Steps

After completing Phase 2, you should have:
1. ✅ Fully functional Leitner algorithm
2. ✅ All edge cases handled
3. ✅ Comprehensive test coverage
4. ✅ Ready for UI integration

**Ready for Phase 3**: Basic UI Components

---

## Additional Resources

### Leitner System
- Wikipedia: https://en.wikipedia.org/wiki/Leitner_system
- Spaced Repetition: https://en.wikipedia.org/wiki/Spaced_repetition

### Testing Best Practices
- Always test edge cases (Box 1, Box 5, incorrect answers)
- Test date calculations with fixed dates
- Verify database state after operations

---

**Phase 2 Complete!** 🎉

Your Leitner spaced repetition system is now fully implemented and tested!
