"""Leitner spaced repetition algorithm implementation."""
from datetime import datetime, date
from typing import List, Optional
from sqlmodel import select, and_

from vocab_stack.models import Flashcard, LeitnerState, ReviewHistory, User
from vocab_stack.utils.date_helpers import calculate_next_review_date, is_due_for_review
import reflex as rx


class LeitnerService:
    """Service for managing Leitner box algorithm."""
    
    @staticmethod
    def get_due_cards(topic_id: Optional[int] = None, user_id: Optional[int] = None, review_order: str = "random") -> List[Flashcard]:
        """
        Get all flashcards due for review today.
        
        Args:
            topic_id: Filter by topic (optional)
            user_id: Filter by user (optional) - NOTE: If topic_id is specified, user_id is ignored
                     to allow users to review all cards in a topic
            review_order: Order of cards - "random", "oldest_first", "newest_first" (default: "random")
            
        Returns:
            List of flashcards due for review
            
        Example:
            >>> cards = LeitnerService.get_due_cards(topic_id=1, user_id=1, review_order="oldest_first")
            >>> print(f"Found {len(cards)} cards to review")
        """
        import random
        
        with rx.session() as session:
            # Build query
            query = select(Flashcard).join(LeitnerState)
            
            # Add filters
            conditions = [LeitnerState.next_review_date <= date.today()]
            
            if topic_id is not None:
                # When reviewing by topic, show all cards in that topic (regardless of owner)
                conditions.append(Flashcard.topic_id == topic_id)
            elif user_id is not None:
                # When no topic specified, only show user's own cards
                conditions.append(Flashcard.user_id == user_id)
            
            query = query.where(and_(*conditions))
            
            # Apply ordering
            if review_order == "oldest_first":
                query = query.order_by(Flashcard.created_at.asc())
            elif review_order == "newest_first":
                query = query.order_by(Flashcard.created_at.desc())
            # For random, we'll shuffle after fetching
            
            # Execute
            cards = session.exec(query).all()
            
            # Shuffle if random order
            if review_order == "random":
                cards_list = list(cards)
                random.shuffle(cards_list)
                return cards_list
            
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
