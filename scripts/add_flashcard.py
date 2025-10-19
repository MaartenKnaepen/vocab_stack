"""Script to add flashcards programmatically."""
import sys
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from datetime import date
from vocab_stack.database import get_session
from vocab_stack.models import Flashcard, LeitnerState, Topic
from sqlmodel import select


def add_flashcard(
    front: str,
    back: str,
    topic_name: str,
    example: str = None,
    user_id: int = 1
) -> int:
    """
    Add a new flashcard programmatically.
    
    Args:
        front: Question/word (required)
        back: Answer/translation (required)
        topic_name: Name of topic (will be created if doesn't exist)
        example: Optional example sentence
        user_id: User ID (default: 1)
        
    Returns:
        Flashcard ID
        
    Example:
        >>> card_id = add_flashcard(
        ...     front="Hello",
        ...     back="Hola",
        ...     topic_name="Spanish Basics",
        ...     example="Hello, how are you?"
        ... )
        >>> print(f"Created card {card_id}")
    """
    with get_session() as session:
        # Get or create topic
        topic = session.exec(
            select(Topic).where(Topic.name == topic_name)
        ).first()
        
        if not topic:
            topic = Topic(name=topic_name, description=f"Auto-created for {topic_name}")
            session.add(topic)
            session.flush()
            print(f"Created new topic: {topic_name}")
        
        # Create flashcard
        card = Flashcard(
            front=front,
            back=back,
            example=example,
            topic_id=topic.id,
            user_id=user_id
        )
        session.add(card)
        session.flush()
        
        # Create initial Leitner state
        leitner = LeitnerState(
            flashcard_id=card.id,
            box_number=1,
            next_review_date=date.today()
        )
        session.add(leitner)
        session.commit()
        
        print(f"✅ Created flashcard: {front} → {back}")
        return card.id


def add_flashcards_bulk(flashcards: list[dict]) -> list[int]:
    """
    Add multiple flashcards at once.
    
    Args:
        flashcards: List of dicts with keys: front, back, topic_name, example (optional)
        
    Returns:
        List of created flashcard IDs
        
    Example:
        >>> cards = [
        ...     {"front": "Hello", "back": "Hola", "topic_name": "Spanish"},
        ...     {"front": "Goodbye", "back": "Adiós", "topic_name": "Spanish"},
        ... ]
        >>> ids = add_flashcards_bulk(cards)
        >>> print(f"Created {len(ids)} cards")
    """
    card_ids = []
    for card_data in flashcards:
        card_id = add_flashcard(
            front=card_data["front"],
            back=card_data["back"],
            topic_name=card_data["topic_name"],
            example=card_data.get("example")
        )
        card_ids.append(card_id)
    return card_ids


if __name__ == "__main__":
    # Example usage
    print("Adding sample flashcards...")
    
    # Single card
    card_id = add_flashcard(
        front="Cat",
        back="Gato",
        topic_name="Spanish Animals",
        example="The cat is sleeping."
    )
    
    # Bulk cards
    spanish_cards = [
        {"front": "Dog", "back": "Perro", "topic_name": "Spanish Animals"},
        {"front": "Bird", "back": "Pájaro", "topic_name": "Spanish Animals"},
        {"front": "Fish", "back": "Pez", "topic_name": "Spanish Animals"},
    ]
    
    ids = add_flashcards_bulk(spanish_cards)
    
    print(f"\n✅ Created {len(ids) + 1} flashcards total")
