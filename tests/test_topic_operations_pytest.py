"""Tests for topic operations including cascade deletion - pytest version."""
import pytest
from vocab_stack.database import get_session, create_db_and_tables, drop_all_tables
from vocab_stack.models import User, Topic, Flashcard, LeitnerState, ReviewHistory
from vocab_stack.services.auth_service import AuthService
from sqlmodel import select
from datetime import date


@pytest.fixture(scope="function")
def setup_user():
    """Set up test database with a user."""
    drop_all_tables()
    create_db_and_tables()
    
    _, _, user = AuthService.register_user("testuser", "test@example.com", "password123")
    
    yield user.id
    
    # Cleanup is optional since each test gets fresh database


class TestTopicOperations:
    """Test topic CRUD operations and cascade deletion."""
    
    def test_create_topic(self, setup_user):
        """Test creating a topic."""
        with get_session() as session:
            topic = Topic(name="Test Topic", description="A test topic")
            session.add(topic)
            session.commit()
            session.refresh(topic)
            
            assert topic.id is not None, "Topic should have an ID"
            assert topic.name == "Test Topic", "Topic name should match"
    
    def test_cascade_deletion(self, setup_user):
        """Test that deleting a topic deletes all related data."""
        user_id = setup_user
        
        # Create topic with cards
        with get_session() as session:
            topic = Topic(name="Delete Test", description="Will be deleted")
            session.add(topic)
            session.commit()
            session.refresh(topic)
            
            topic_id = topic.id
            flashcard_ids = []
            
            # Add 5 flashcards
            for i in range(5):
                card = Flashcard(
                    front=f"Question {i+1}",
                    back=f"Answer {i+1}",
                    topic_id=topic.id,
                    user_id=user_id
                )
                session.add(card)
                session.flush()
                flashcard_ids.append(card.id)
                
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
                    user_id=user_id,
                    was_correct=True
                )
                session.add(review)
            
            session.commit()
        
        # Perform cascade deletion
        with get_session() as session:
            topic = session.get(Topic, topic_id)
            
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
            topic = session.get(Topic, topic_id)
            assert topic is None, "Topic should be deleted"
            
            # Flashcards should be gone
            cards = session.exec(
                select(Flashcard).where(Flashcard.topic_id == topic_id)
            ).all()
            assert len(cards) == 0, f"All flashcards should be deleted, found {len(cards)}"
            
            # Leitner states should be gone
            for card_id in flashcard_ids:
                leitner_states = session.exec(
                    select(LeitnerState).where(LeitnerState.flashcard_id == card_id)
                ).all()
                assert len(leitner_states) == 0, \
                    f"All Leitner states should be deleted, found {len(leitner_states)}"
            
            # Review history should be gone
            for card_id in flashcard_ids:
                reviews = session.exec(
                    select(ReviewHistory).where(ReviewHistory.flashcard_id == card_id)
                ).all()
                assert len(reviews) == 0, \
                    f"All review history should be deleted, found {len(reviews)}"
    
    def test_topic_deletion_doesnt_affect_other_topics(self, setup_user):
        """Test that deleting one topic doesn't affect other topics."""
        user_id = setup_user
        
        with get_session() as session:
            # Create two topics with cards
            topic1 = Topic(name="Topic 1", description="First topic")
            topic2 = Topic(name="Topic 2", description="Second topic")
            session.add(topic1)
            session.add(topic2)
            session.commit()
            session.refresh(topic1)
            session.refresh(topic2)
            
            topic1_id = topic1.id
            topic2_id = topic2.id
            
            # Add cards to both topics
            for i in range(3):
                card1 = Flashcard(
                    front=f"Topic1 Q{i}",
                    back=f"Topic1 A{i}",
                    topic_id=topic1.id,
                    user_id=user_id
                )
                card2 = Flashcard(
                    front=f"Topic2 Q{i}",
                    back=f"Topic2 A{i}",
                    topic_id=topic2.id,
                    user_id=user_id
                )
                session.add(card1)
                session.add(card2)
                session.flush()
                
                # Add Leitner states
                session.add(LeitnerState(flashcard_id=card1.id, box_number=1))
                session.add(LeitnerState(flashcard_id=card2.id, box_number=1))
            
            session.commit()
        
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
    
    def test_reverse_topic(self, setup_user):
        """Test creating a reversed topic with front/back swapped."""
        user_id = setup_user
        
        # Create source topic with cards
        with get_session() as session:
            source_topic = Topic(name="Spanish Basics", description="Basic Spanish")
            session.add(source_topic)
            session.commit()
            session.refresh(source_topic)
            
            # Add test cards
            cards_data = [
                ("Hello", "Hola"),
                ("Goodbye", "Adiós"),
                ("Thank you", "Gracias"),
                ("Please", "Por favor"),
            ]
            
            for front, back in cards_data:
                card = Flashcard(
                    front=front,
                    back=back,
                    topic_id=source_topic.id,
                    user_id=user_id
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
            
            session.commit()
            source_topic_id = source_topic.id
        
        # Create reversed topic
        with get_session() as session:
            source_topic = session.get(Topic, source_topic_id)
            
            # Create new topic
            new_topic = Topic(
                name=f"{source_topic.name} (Reversed)",
                description=f"Reversed from: {source_topic.description or source_topic.name}"
            )
            session.add(new_topic)
            session.flush()
            
            # Get source cards
            source_cards = session.exec(
                select(Flashcard).where(Flashcard.topic_id == source_topic_id)
            ).all()
            
            # Create reversed cards
            for source_card in source_cards:
                new_card = Flashcard(
                    front=source_card.back,  # Swap!
                    back=source_card.front,   # Swap!
                    example=source_card.example,
                    topic_id=new_topic.id,
                    user_id=user_id
                )
                session.add(new_card)
                session.flush()
                session.refresh(new_card)
                
                # Create Leitner state
                leitner = LeitnerState(
                    flashcard_id=new_card.id,
                    box_number=1,
                    next_review_date=date.today()
                )
                session.add(leitner)
            
            session.commit()
            new_topic_id = new_topic.id
        
        # Verify the reversed topic
        with get_session() as session:
            new_topic = session.get(Topic, new_topic_id)
            assert new_topic is not None, "Reversed topic should exist"
            assert "(Reversed)" in new_topic.name, "Topic name should indicate it's reversed"
            
            # Get both sets of cards
            source_cards = session.exec(
                select(Flashcard).where(Flashcard.topic_id == source_topic_id)
            ).all()
            reversed_cards = session.exec(
                select(Flashcard).where(Flashcard.topic_id == new_topic_id)
            ).all()
            
            assert len(source_cards) == len(reversed_cards), \
                "Reversed topic should have same number of cards"
            assert len(reversed_cards) == 4, f"Should have 4 reversed cards, found {len(reversed_cards)}"
            
            # Verify each card is properly reversed
            source_dict = {card.front: card.back for card in source_cards}
            for rev_card in reversed_cards:
                # The reversed card's front should be in the source's backs
                # And the reversed card's back should match the source's front
                assert rev_card.back in source_dict, \
                    f"Reversed card back '{rev_card.back}' should be a source front"
                assert source_dict[rev_card.back] == rev_card.front, \
                    f"Reversed card front '{rev_card.front}' should match source back"
            
            # Verify Leitner states exist for all reversed cards
            for card in reversed_cards:
                leitner = session.exec(
                    select(LeitnerState).where(LeitnerState.flashcard_id == card.id)
                ).first()
                assert leitner is not None, f"Card {card.id} should have Leitner state"
                assert leitner.box_number == 1, "New cards should start in box 1"
