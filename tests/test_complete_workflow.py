"""Complete workflow integration tests."""
import sys
sys.path.insert(0, '.')

from datetime import date
from vocab_stack.database import get_session, create_db_and_tables
from vocab_stack.models import User, Topic, Flashcard, LeitnerState, ReviewHistory
from vocab_stack.services.leitner_service import LeitnerService
from vocab_stack.services.statistics_service import StatisticsService
from vocab_stack.services.settings_service import SettingsService
from sqlmodel import select


def test_complete_learning_workflow():
    """Test complete user workflow."""
    print("\n" + "=" * 70)
    print("🧪 Testing Complete Learning Workflow")
    print("=" * 70)
    
    create_db_and_tables()
    
    # Step 1: Create user
    print("\n1️⃣  Creating user...")
    with get_session() as session:
        # Check if user exists first
        existing = session.exec(
            select(User).where(User.username == "test_workflow")
        ).first()
        
        if existing:
            user_id = existing.id
            print(f"   Using existing user: {user_id}")
        else:
            user = User(username="test_workflow", email="workflow@test.com")
            session.add(user)
            session.commit()
            session.refresh(user)
            user_id = user.id
            print(f"   User created: {user_id}")
    print("✅ User ready")
    
    # Step 2: Create topic
    print("\n2️⃣  Creating topic...")
    with get_session() as session:
        # Check if topic exists
        existing = session.exec(
            select(Topic).where(Topic.name == "Test Workflow Topic")
        ).first()
        
        if existing:
            topic_id = existing.id
            print(f"   Using existing topic: {topic_id}")
        else:
            topic = Topic(name="Test Workflow Topic", description="For testing")
            session.add(topic)
            session.commit()
            session.refresh(topic)
            topic_id = topic.id
            print(f"   Topic created: {topic_id}")
    print("✅ Topic ready")
    
    # Step 3: Create flashcards
    print("\n3️⃣  Creating flashcards...")
    with get_session() as session:
        # Check existing cards for this topic/user
        existing_count = session.exec(
            select(Flashcard).where(
                Flashcard.topic_id == topic_id,
                Flashcard.user_id == user_id
            )
        ).all()
        
        if len(existing_count) >= 10:
            print(f"   Using existing {len(existing_count)} flashcards")
        else:
            cards_to_create = 10 - len(existing_count)
            for i in range(cards_to_create):
                card = Flashcard(
                    front=f"Question {len(existing_count) + i + 1}",
                    back=f"Answer {len(existing_count) + i + 1}",
                    example=f"Example {len(existing_count) + i + 1}",
                    topic_id=topic_id,
                    user_id=user_id
                )
                session.add(card)
                session.flush()
                
                # Check if leitner state exists
                existing_leitner = session.exec(
                    select(LeitnerState).where(LeitnerState.flashcard_id == card.id)
                ).first()
                
                if not existing_leitner:
                    leitner = LeitnerState(
                        flashcard_id=card.id,
                        box_number=1,
                        next_review_date=date.today()
                    )
                    session.add(leitner)
            
            session.commit()
            print(f"   Created {cards_to_create} new flashcards")
    print("✅ Flashcards ready")
    
    # Step 4: Simulate review session
    print("\n4️⃣  Simulating review session...")
    due_cards = LeitnerService.get_due_cards(user_id=user_id, topic_id=topic_id)
    print(f"   Found {len(due_cards)} cards due")
    
    if len(due_cards) > 0:
        correct = 0
        incorrect = 0
        for i, card in enumerate(due_cards[:5]):
            was_correct = i % 2 == 0  # Alternate correct/incorrect
            result = LeitnerService.process_review(
                flashcard_id=card.id,
                user_id=user_id,
                was_correct=was_correct,
                time_spent_seconds=10
            )
            
            if was_correct:
                correct += 1
            else:
                incorrect += 1
            
            print(f"   Card {i+1}: Box {result['old_box']} → {result['new_box']}")
        
        print(f"✅ Review session complete: {correct} correct, {incorrect} incorrect")
    else:
        print("⚠️  No cards due for review (cards may have been reviewed recently)")
    
    # Step 5: Check statistics
    print("\n5️⃣  Checking statistics...")
    stats = StatisticsService.get_user_overview(user_id)
    print(f"   Total cards: {stats['total_cards']}")
    print(f"   Total reviews: {stats['total_reviews']}")
    print(f"   Accuracy: {stats['overall_accuracy']}%")
    print(f"   Box distribution: {stats['box_distribution']}")
    print("✅ Statistics calculated")
    
    # Step 6: Update settings
    print("\n6️⃣  Updating user settings...")
    settings = {
        "cards_per_session": 15,
        "daily_goal": 75,
        "show_examples": False,
    }
    success = SettingsService.update_user_settings(user_id, settings)
    assert success, "Settings update failed"
    print("✅ Settings updated")
    
    # Step 7: Verify settings
    print("\n7️⃣  Verifying settings...")
    loaded_settings = SettingsService.get_user_settings(user_id)
    assert loaded_settings["cards_per_session"] == 15, "cards_per_session mismatch"
    assert loaded_settings["daily_goal"] == 75, "daily_goal mismatch"
    assert loaded_settings["show_examples"] == False, "show_examples mismatch"
    print("✅ Settings verified")
    
    # Step 8: Check topic progress
    print("\n8️⃣  Checking topic progress...")
    progress = LeitnerService.get_topic_progress(topic_id, user_id)
    print(f"   Total cards: {progress['total']}")
    print(f"   Due today: {progress['due_today']}")
    print(f"   Mastered: {progress['mastered']}")
    print(f"   By box: {progress['by_box']}")
    print("✅ Topic progress retrieved")
    
    print("\n" + "=" * 70)
    print("✅ Complete Workflow Test Passed!")
    print("=" * 70)


def test_edge_cases():
    """Test edge cases and error handling."""
    print("\n" + "=" * 70)
    print("🧪 Testing Edge Cases")
    print("=" * 70)
    
    # Test 1: No cards due
    print("\n1️⃣  Testing no cards due...")
    due_cards = LeitnerService.get_due_cards(user_id=999, topic_id=999)
    assert len(due_cards) == 0
    print("✅ Handles no cards gracefully")
    
    # Test 2: Invalid card ID
    print("\n2️⃣  Testing invalid card ID...")
    try:
        LeitnerService.process_review(999999, 1, True)
        assert False, "Should have raised error"
    except ValueError:
        print("✅ Raises error for invalid card")
    
    # Test 3: Topic with no cards
    print("\n3️⃣  Testing topic with no cards...")
    progress = LeitnerService.get_topic_progress(999, 1)
    assert progress["total"] == 0
    print("✅ Handles empty topic")
    
    # Test 4: Statistics with no data
    print("\n4️⃣  Testing statistics with no data...")
    stats = StatisticsService.get_user_overview(999)
    assert stats["total_cards"] == 0
    assert stats["overall_accuracy"] == 0
    print("✅ Handles no data gracefully")
    
    # Test 5: Settings for non-existent user
    print("\n5️⃣  Testing settings for non-existent user...")
    settings = SettingsService.get_user_settings(999)
    assert settings == {}
    print("✅ Handles missing user gracefully")
    
    print("\n" + "=" * 70)
    print("✅ All Edge Case Tests Passed!")
    print("=" * 70)


if __name__ == "__main__":
    try:
        test_complete_learning_workflow()
        test_edge_cases()
        print("\n🎉 All tests passed successfully!")
    except Exception as e:
        print(f"\n❌ Test failed: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
