# API and Integration Guide

## Overview
This guide explains how to add flashcards to the Vocabulary Learning App programmatically, integrate with external systems, and extend functionality.

---

## Quick Answer: How to Add Flashcards

### Method 1: Web UI (Easiest)
Navigate to http://localhost:3000/cards and use the "New Card" button.

### Method 2: CSV Import (Bulk)
```bash
python scripts/import_csv.py my_flashcards.csv
```

### Method 3: Python Script
```python
from scripts.add_flashcard import add_flashcard

add_flashcard(
    front="Hello",
    back="Hola",
    topic_name="Spanish",
    example="Hello, how are you?"
)
```

---

## Current API Status

### No REST API Yet ❌
The app currently does **NOT** have a REST/HTTP API. However, you have several programmatic options:

✅ **Available Now:**
- Web UI (manual entry)
- Python scripts (programmatic)
- CSV import (bulk)
- Direct database access (advanced)

⏳ **Future Enhancement:**
- REST API with FastAPI endpoints

---

## Working Methods (Tested ✅)

### 1. CSV Import Script

**Location**: `scripts/import_csv.py`

**Create Sample CSV:**
```bash
python scripts/import_csv.py --create-sample
```

**Import CSV:**
```bash
python scripts/import_csv.py your_cards.csv
```

**CSV Format:**
```csv
front,back,topic,example
Hello,Hola,Spanish Basics,Hello how are you?
Goodbye,Adiós,Spanish Basics,Goodbye my friend
```

**Features:**
- ✅ Bulk import
- ✅ Auto-creates topics
- ✅ Progress tracking
- ✅ UTF-8 support
- ✅ Error handling

**Output:**
```
   Created topic: Spanish Basics
   Imported 10 cards...
   
✅ Successfully imported 25 flashcards
🎉 Import complete! 25 cards added to your deck.
```

### 2. Python Add Flashcard Script

**Location**: `scripts/add_flashcard.py`

**Single Card:**
```python
from scripts.add_flashcard import add_flashcard

card_id = add_flashcard(
    front="Hello",
    back="Hola",
    topic_name="Spanish Basics",
    example="Hello, how are you?"
)
```

**Bulk Cards:**
```python
from scripts.add_flashcard import add_flashcards_bulk

cards = [
    {"front": "Cat", "back": "Gato", "topic_name": "Animals"},
    {"front": "Dog", "back": "Perro", "topic_name": "Animals"},
    {"front": "Bird", "back": "Pájaro", "topic_name": "Animals"},
]

ids = add_flashcards_bulk(cards)
print(f"Created {len(ids)} cards")
```

**Run Sample:**
```bash
python scripts/add_flashcard.py
```

**Output:**
```
✅ Created flashcard: Cat → Gato
✅ Created flashcard: Dog → Perro
✅ Created flashcard: Bird → Pájaro
✅ Created flashcard: Fish → Pez

✅ Created 4 flashcards total
```

### 3. Direct Database Access (Advanced)

For custom integrations:

```python
from datetime import date
from vocab_stack.database import get_session
from vocab_stack.models import Flashcard, LeitnerState, Topic
from sqlmodel import select

with get_session() as session:
    # Get or create topic
    topic = session.exec(
        select(Topic).where(Topic.name == "My Topic")
    ).first()
    
    if not topic:
        topic = Topic(name="My Topic")
        session.add(topic)
        session.flush()
    
    # Create flashcard
    card = Flashcard(
        front="Question",
        back="Answer",
        example="Example sentence",
        topic_id=topic.id,
        user_id=1
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
    session.commit()
```

---

## Integration Examples

### Example 1: Import from Spreadsheet

**Step 1:** Export Google Sheets/Excel to CSV
- File → Download → CSV

**Step 2:** Format CSV with required columns
```csv
front,back,topic,example
word1,translation1,topic1,example1
word2,translation2,topic2,example2
```

**Step 3:** Import
```bash
python scripts/import_csv.py my_export.csv
```

### Example 2: Scrape Vocabulary from Website

```python
import requests
from bs4 import BeautifulSoup
from scripts.add_flashcard import add_flashcard

# Fetch page
response = requests.get('https://example.com/vocab-list')
soup = BeautifulSoup(response.text, 'html.parser')

# Parse and create cards
for item in soup.find_all('div', class_='vocab-item'):
    front = item.find('span', class_='english').text
    back = item.find('span', class_='translation').text
    
    add_flashcard(
        front=front,
        back=back,
        topic_name="Web Scraped Vocabulary"
    )
```

### Example 3: Generate from Dictionary API

```python
import requests
from scripts.add_flashcard import add_flashcard

words = ["hello", "goodbye", "thank you"]

for word in words:
    # Fetch from dictionary API
    response = requests.get(
        f'https://api.dictionaryapi.dev/api/v2/entries/en/{word}'
    )
    data = response.json()[0]
    
    definition = data['meanings'][0]['definitions'][0]['definition']
    example = data['meanings'][0]['definitions'][0].get('example', '')
    
    add_flashcard(
        front=word,
        back=definition,
        topic_name="Dictionary Definitions",
        example=example
    )
```

### Example 4: Migrate from Anki

Anki exports TSV (tab-separated):

```python
import csv
from scripts.add_flashcard import add_flashcards_bulk

flashcards = []

with open('anki_export.txt', 'r', encoding='utf-8') as f:
    reader = csv.reader(f, delimiter='\t')
    
    for row in reader:
        if len(row) >= 2:
            flashcards.append({
                "front": row[0],
                "back": row[1],
                "topic_name": "Anki Import",
                "example": row[2] if len(row) > 2 else None
            })

ids = add_flashcards_bulk(flashcards)
print(f"Migrated {len(ids)} cards from Anki")
```

---

## Future: REST API Implementation

### Proposed Endpoints

If a REST API were to be added, it would look like this:

**POST /api/flashcards** - Create flashcard
```json
{
  "front": "Hello",
  "back": "Hola",
  "topic_name": "Spanish",
  "example": "Hello, how are you?"
}
```

**GET /api/flashcards** - List flashcards
```
Query params: ?topic=Spanish&limit=50
```

**GET /api/flashcards/{id}** - Get single flashcard

**PUT /api/flashcards/{id}** - Update flashcard

**DELETE /api/flashcards/{id}** - Delete flashcard

**POST /api/flashcards/bulk** - Bulk create
```json
{
  "flashcards": [
    {"front": "...", "back": "...", "topic_name": "..."},
    {"front": "...", "back": "...", "topic_name": "..."}
  ]
}
```

### Implementation Sketch

```python
# In vocab_stack/api.py (not yet created)
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from datetime import date
from vocab_stack.database import get_session
from vocab_stack.models import Flashcard, LeitnerState, Topic
from sqlmodel import select

api = FastAPI()

class FlashcardCreate(BaseModel):
    front: str
    back: str
    topic_name: str
    example: str | None = None

@api.post("/api/flashcards")
def create_flashcard(card: FlashcardCreate):
    """Create a new flashcard."""
    with get_session() as session:
        # Get or create topic
        topic = session.exec(
            select(Topic).where(Topic.name == card.topic_name)
        ).first()
        
        if not topic:
            topic = Topic(name=card.topic_name)
            session.add(topic)
            session.flush()
        
        # Create flashcard
        new_card = Flashcard(
            front=card.front,
            back=card.back,
            example=card.example,
            topic_id=topic.id,
            user_id=1  # Would come from auth
        )
        session.add(new_card)
        session.flush()
        
        # Create Leitner state
        leitner = LeitnerState(
            flashcard_id=new_card.id,
            box_number=1,
            next_review_date=date.today()
        )
        session.add(leitner)
        session.commit()
        
        return {"id": new_card.id, "message": "Flashcard created"}

@api.get("/api/flashcards")
def list_flashcards(topic: str | None = None, limit: int = 50):
    """List flashcards."""
    with get_session() as session:
        query = select(Flashcard).limit(limit)
        
        if topic:
            query = query.join(Topic).where(Topic.name == topic)
        
        cards = session.exec(query).all()
        return [
            {
                "id": c.id,
                "front": c.front,
                "back": c.back,
                "example": c.example,
                "topic": c.topic.name
            }
            for c in cards
        ]
```

### Usage Example (if implemented)

```bash
# Create flashcard
curl -X POST http://localhost:8000/api/flashcards \
  -H "Content-Type: application/json" \
  -d '{
    "front": "Hello",
    "back": "Hola",
    "topic_name": "Spanish",
    "example": "Hello, how are you?"
  }'

# List flashcards
curl http://localhost:8000/api/flashcards?topic=Spanish&limit=10

# Delete flashcard
curl -X DELETE http://localhost:8000/api/flashcards/123
```

---

## Comparison of Integration Methods

| Method | Best For | Speed | Setup | Authentication |
|--------|----------|-------|-------|----------------|
| **Web UI** | End users | Slow | None | Not needed |
| **CSV Import** | Bulk data | Fast | CSV file | Not needed |
| **Python Script** | Automation | Fast | Python env | Not needed |
| **Direct DB** | Custom logic | Fast | Python env | Not needed |
| **REST API** | External apps | Fast | HTTP client | Would need auth |

---

## Security Considerations

### Current State (user_id=1)
- All methods currently hardcode user_id=1
- No authentication required
- Suitable for single-user/development use

### Production Considerations
When deploying for multiple users:
1. Implement authentication (JWT, sessions)
2. Validate user_id from auth context
3. Enforce user-based data isolation
4. Add rate limiting on API endpoints
5. Validate and sanitize all inputs

---

## Testing Integration

### Test CSV Import
```bash
# Create sample
python scripts/import_csv.py --create-sample

# Import sample
python scripts/import_csv.py sample_flashcards.csv

# Verify in app
# Navigate to http://localhost:3000/cards
```

### Test Python Script
```bash
# Run example
python scripts/add_flashcard.py

# Verify in app
# Navigate to http://localhost:3000/cards
# Filter by "Spanish Animals" topic
```

### Test Direct Access
```python
# Run in Python REPL
from vocab_stack.database import get_session
from vocab_stack.models import Flashcard
from sqlmodel import select

with get_session() as session:
    cards = session.exec(select(Flashcard)).all()
    print(f"Total cards: {len(cards)}")
    for card in cards[:5]:
        print(f"  {card.front} → {card.back}")
```

---

## Troubleshooting

### Import Not Working?
- Check CSV format (headers: front, back, topic, example)
- Verify file encoding (UTF-8)
- Check console for error messages

### Cards Not Appearing?
- Verify they were created (check console output)
- Refresh the Cards page
- Check user_id (should be 1)

### Topic Not Created?
- Topics are auto-created by all methods
- Case-sensitive (ensure exact match)

---

## Summary

### ✅ Currently Available
1. **CSV Import** - `scripts/import_csv.py` (tested, working)
2. **Python Script** - `scripts/add_flashcard.py` (tested, working)
3. **Direct Database** - SQLModel code (advanced users)
4. **Web UI** - Manual entry at `/cards` page

### ⏳ Future Enhancement
5. **REST API** - HTTP endpoints (not yet implemented)

### 📚 Documentation
- Complete guide: `docs/adding_flashcards_guide.md`
- This file: Technical integration details
- Scripts: Fully functional with examples

---

**For detailed examples and CSV format, see `docs/adding_flashcards_guide.md`**
