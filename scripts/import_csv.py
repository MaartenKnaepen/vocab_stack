"""Import flashcards from CSV file."""
import csv
import sys
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from datetime import date
from vocab_stack.database import get_session
from vocab_stack.models import Flashcard, LeitnerState, Topic
from sqlmodel import select


def import_from_csv(csv_file: str, user_id: int = 1) -> int:
    """
    Import flashcards from a CSV file.
    
    CSV Format:
        front,back,topic,example
        Hello,Hola,Spanish Basics,Hello how are you?
        Goodbye,Adiós,Spanish Basics,Goodbye my friend
        
    Args:
        csv_file: Path to CSV file
        user_id: User ID (default: 1)
        
    Returns:
        Number of cards imported
    """
    imported_count = 0
    topics_cache = {}  # Cache topics to avoid repeated queries
    
    try:
        with open(csv_file, 'r', encoding='utf-8') as f:
            reader = csv.DictReader(f)
            
            # Validate headers
            required_fields = {'front', 'back', 'topic'}
            if not required_fields.issubset(set(reader.fieldnames)):
                print(f"❌ Error: CSV must have columns: {required_fields}")
                print(f"   Found columns: {reader.fieldnames}")
                return 0
            
            with get_session() as session:
                for row_num, row in enumerate(reader, start=2):  # Start at 2 (header is row 1)
                    front = row['front'].strip()
                    back = row['back'].strip()
                    topic_name = row['topic'].strip()
                    example = row.get('example', '').strip() or None
                    
                    # Validate required fields
                    if not front or not back or not topic_name:
                        print(f"⚠️  Skipping row {row_num}: Missing required field")
                        continue
                    
                    # Get or create topic
                    if topic_name not in topics_cache:
                        topic = session.exec(
                            select(Topic).where(Topic.name == topic_name)
                        ).first()
                        
                        if not topic:
                            topic = Topic(name=topic_name, description=f"Imported from CSV")
                            session.add(topic)
                            session.flush()
                            print(f"   Created topic: {topic_name}")
                        
                        topics_cache[topic_name] = topic.id
                    
                    topic_id = topics_cache[topic_name]
                    
                    # Create flashcard
                    card = Flashcard(
                        front=front,
                        back=back,
                        example=example,
                        topic_id=topic_id,
                        user_id=user_id
                    )
                    session.add(card)
                    session.flush()
                    
                    # Create Leitner state
                    leitner = LeitnerState(
                        flashcard_id=card.id,
                        box_number=1,
                        next_review_date=date.today()
                    )
                    session.add(leitner)
                    
                    imported_count += 1
                    
                    if imported_count % 10 == 0:
                        print(f"   Imported {imported_count} cards...")
                
                session.commit()
        
        print(f"\n✅ Successfully imported {imported_count} flashcards")
        return imported_count
        
    except FileNotFoundError:
        print(f"❌ Error: File not found: {csv_file}")
        return 0
    except Exception as e:
        print(f"❌ Error importing CSV: {e}")
        import traceback
        traceback.print_exc()
        return 0


def create_sample_csv(filename: str = "sample_flashcards.csv"):
    """Create a sample CSV file for reference."""
    sample_data = [
        {"front": "Hello", "back": "Hola", "topic": "Spanish Basics", "example": "Hello, how are you?"},
        {"front": "Goodbye", "back": "Adiós", "topic": "Spanish Basics", "example": "Goodbye, see you later"},
        {"front": "Thank you", "back": "Gracias", "topic": "Spanish Basics", "example": "Thank you very much"},
        {"front": "Cat", "back": "Gato", "topic": "Spanish Animals", "example": "The cat is sleeping"},
        {"front": "Dog", "back": "Perro", "topic": "Spanish Animals", "example": "My dog is friendly"},
    ]
    
    with open(filename, 'w', encoding='utf-8', newline='') as f:
        writer = csv.DictWriter(f, fieldnames=['front', 'back', 'topic', 'example'])
        writer.writeheader()
        writer.writerows(sample_data)
    
    print(f"✅ Created sample CSV: {filename}")


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage:")
        print("  python scripts/import_csv.py <csv_file>")
        print("  python scripts/import_csv.py --create-sample")
        print("\nCSV Format:")
        print("  front,back,topic,example")
        print("  Hello,Hola,Spanish Basics,Hello how are you?")
        sys.exit(1)
    
    if sys.argv[1] == "--create-sample":
        create_sample_csv()
    else:
        csv_file = sys.argv[1]
        count = import_from_csv(csv_file)
        if count > 0:
            print(f"\n🎉 Import complete! {count} cards added to your deck.")
