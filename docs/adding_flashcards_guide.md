# Adding Flashcards - Complete Guide

## Overview
This guide explains all the different ways to add flashcards to your Vocabulary Learning App.

---

## Method 1: Web Interface (UI) ✅

### Via Cards Page
The easiest way for end users.

**Steps:**
1. Navigate to http://localhost:3000/cards
2. Click "New Card" button
3. Fill in the form:
   - **Front**: Question/word (e.g., "Hello")
   - **Back**: Answer/translation (e.g., "Hola")
   - **Example**: Optional (e.g., "Hello, how are you?")
   - **Topic**: Select from dropdown
4. Click "Create"

**Features:**
- ✅ User-friendly interface
- ✅ Real-time validation
- ✅ Topic selection dropdown
- ✅ Success/error notifications
- ✅ Automatic Leitner state initialization

**Behind the Scenes:**
```python
CardState.create_card()
    ↓
Validates inputs
    ↓
Creates Flashcard in database
    ↓
Creates LeitnerState (Box 1, due today)
    ↓
Reloads card list
```

---

## Method 2: Programmatic (Python Script) ✅

### Using `scripts/add_flashcard.py`

**Single Card:**
```python
from scripts.add_flashcard import add_flashcard

card_id = add_flashcard(
    front="Hello",
    back="Hola",
    topic_name="Spanish Basics",
    example="Hello, how are you?"
)
print(f"Created card {card_id}")
```

**Bulk Cards:**
```python
from scripts.add_flashcard import add_flashcards_bulk

cards = [
    {"front": "Hello", "back": "Hola", "topic_name": "Spanish"},
    {"front": "Goodbye", "back": "Adiós", "topic_name": "Spanish"},
    {"front": "Thank you", "back": "Gracias", "topic_name": "Spanish"},
]

ids = add_flashcards_bulk(cards)
print(f"Created {len(ids)} cards")
```

**Run from Command Line:**
```bash
# Edit the script to add your cards
python scripts/add_flashcard.py
```

**Features:**
- ✅ Fast bulk creation
- ✅ Auto-creates topics if they don't exist
- ✅ Returns card IDs
- ✅ Error handling
- ✅ Progress feedback

---

## Method 3: CSV Import ✅

### Using `scripts/import_csv.py`

**CSV Format:**
```csv
front,back,topic,example
Hello,Hola,Spanish Basics,Hello how are you?
Goodbye,Adiós,Spanish Basics,Goodbye my friend
Thank you,Gracias,Spanish Basics,Thank you very much
Cat,Gato,Spanish Animals,The cat is sleeping
Dog,Perro,Spanish Animals,My dog is friendly
```

**Create Sample CSV:**
```bash
python scripts/import_csv.py --create-sample
# Creates sample_flashcards.csv
```

**Import CSV:**
```bash
python scripts/import_csv.py your_flashcards.csv
```

**Output:**
```
   Created topic: Spanish Basics
   Created topic: Spanish Animals
   Imported 10 cards...
   Imported 20 cards...

✅ Successfully imported 25 flashcards

🎉 Import complete! 25 cards added to your deck.
```

**Features:**
- ✅ Bulk import from spreadsheets
- ✅ Auto-creates topics
- ✅ Progress tracking
- ✅ Error handling (skips invalid rows)
- ✅ UTF-8 support (works with any language)

**CSV Tips:**
- Use Excel, Google Sheets, or any text editor
- Export as CSV (UTF-8)
- Required columns: front, back, topic
- Optional column: example
- Empty examples are allowed

---

## Method 4: Direct Database Access

### Using SQLModel Directly

For advanced users who want full control:

```python
from datetime import date
from vocab_stack.database import get_session
from vocab_stack.models import Flashcard, LeitnerState, Topic
from sqlmodel import select

with get_session() as session:
    # Get or create topic
    topic = session.exec(
        select(Topic).where(Topic.name == "Spanish")
    ).first()
    
    if not topic:
        topic = Topic(name="Spanish", description="Spanish vocabulary")
        session.add(topic)
        session.flush()
    
    # Create flashcard
    card = Flashcard(
        front="Hello",
        back="Hola",
        example="Hello, how are you?",
        topic_id=topic.id,
        user_id=1  # Hardcoded for demo
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
    
    print(f"Created card: {card.id}")
```

**When to Use:**
- Custom import logic
- Integration with other systems
- Migration from other apps
- Advanced automation

---

## Method 5: REST API (Future Enhancement)

### Not Yet Implemented

To add a REST API, you would need to add endpoints:

**Proposed API Structure:**
```python
# In a new file: vocab_stack/api.py
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel

api = FastAPI()

class FlashcardCreate(BaseModel):
    front: str
    back: str
    topic_name: str
    example: str | None = None

@api.post("/api/flashcards")
def create_flashcard(card: FlashcardCreate):
    """Create a new flashcard via REST API."""
    # Implementation here
    pass

@api.get("/api/flashcards")
def list_flashcards(topic: str | None = None):
    """List flashcards, optionally filtered by topic."""
    pass

@api.delete("/api/flashcards/{card_id}")
def delete_flashcard(card_id: int):
    """Delete a flashcard."""
    pass
```

**Usage Example (if implemented):**
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
curl http://localhost:8000/api/flashcards?topic=Spanish
```

---

## Comparison of Methods

| Method | Best For | Speed | Difficulty | Bulk Support |
|--------|----------|-------|------------|--------------|
| **Web UI** | End users | Slow | Easy | No |
| **Python Script** | Developers | Fast | Medium | Yes |
| **CSV Import** | Bulk data | Fast | Easy | Yes |
| **Direct DB** | Advanced | Fast | Hard | Yes |
| **REST API** | Integrations | Fast | Easy | Yes (not implemented) |

---

## Common Workflows

### Workflow 1: Manual Entry (Small Deck)
For learning a few words:
1. Use Web UI
2. Create cards one by one
3. Review immediately

### Workflow 2: Importing Existing Deck (Large Deck)
For migrating from another app or spreadsheet:
1. Export to CSV from source
2. Format CSV (front, back, topic, example)
3. Run `python scripts/import_csv.py my_deck.csv`
4. Verify in Web UI

### Workflow 3: Programmatic Creation (Automation)
For generating cards from external sources:
1. Write Python script using `add_flashcard()`
2. Fetch data from API/database/file
3. Create cards in batch
4. Log results

### Workflow 4: Collaborative Deck Building
For teams:
1. Create shared Google Sheet or Excel file
2. Each person adds rows
3. Export to CSV
4. Import using CSV script
5. Share database file

---

## Advanced Examples

### Example 1: Import from Anki Export

Anki exports to TSV (tab-separated). Convert it:

```python
import csv

# Read Anki TSV
with open('anki_export.txt', 'r', encoding='utf-8') as f:
    reader = csv.reader(f, delimiter='\t')
    flashcards = []
    
    for row in reader:
        if len(row) >= 2:
            flashcards.append({
                "front": row[0],
                "back": row[1],
                "topic_name": "Anki Import",
                "example": row[2] if len(row) > 2 else None
            })

# Import using bulk function
from scripts.add_flashcard import add_flashcards_bulk
ids = add_flashcards_bulk(flashcards)
print(f"Imported {len(ids)} cards from Anki")
```

### Example 2: Scrape from Website

```python
import requests
from bs4 import BeautifulSoup
from scripts.add_flashcard import add_flashcard

# Fetch vocabulary list from website
response = requests.get('https://example.com/spanish-words')
soup = BeautifulSoup(response.text, 'html.parser')

# Parse and create cards
for word_element in soup.find_all('div', class_='word'):
    front = word_element.find('span', class_='english').text
    back = word_element.find('span', class_='spanish').text
    
    add_flashcard(
        front=front,
        back=back,
        topic_name="Web Scraped"
    )
```

### Example 3: Generate from Dictionary API

```python
import requests
from scripts.add_flashcard import add_flashcard

words = ["hello", "goodbye", "thank you"]

for word in words:
    # Fetch definition from API
    response = requests.get(f'https://api.dictionaryapi.dev/api/v2/entries/en/{word}')
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

---

## Validation Rules

All methods enforce these rules:

### Required Fields
- ✅ `front` - Must not be empty
- ✅ `back` - Must not be empty
- ✅ `topic` - Must be specified

### Optional Fields
- ⚪ `example` - Can be empty or omitted

### Auto-Generated
- 🔧 `created_at` - Timestamp
- 🔧 `user_id` - Defaults to 1
- 🔧 `leitner_state` - Box 1, due today

### Topics
- 🔄 **Auto-created** if they don't exist
- 🔄 **Reused** if they already exist
- 🔄 Case-sensitive matching

---

## Error Handling

### Common Errors

**1. Empty Required Field**
```
❌ Error: Front text cannot be empty
Solution: Provide valid front text
```

**2. Topic Selection Missing (UI)**
```
❌ Error: Please select a topic
Solution: Choose a topic from dropdown
```

**3. CSV Format Error**
```
❌ Error: CSV must have columns: {'front', 'back', 'topic'}
Solution: Add missing column headers
```

**4. File Not Found (CSV)**
```
❌ Error: File not found: my_cards.csv
Solution: Check file path and name
```

### Graceful Degradation

All methods handle errors gracefully:
- ✅ Invalid rows skipped (CSV import)
- ✅ User-friendly error messages
- ✅ Transaction rollback on failure
- ✅ Partial import success reported

---

## Best Practices

### 1. Use Consistent Topics
```
✅ Good: "Spanish Basics", "Spanish Animals", "Spanish Verbs"
❌ Bad: "spanish", "Spanish", "SPANISH" (creates 3 topics)
```

### 2. Write Clear Fronts/Backs
```
✅ Good:
   Front: "to run"
   Back: "correr"

❌ Ambiguous:
   Front: "run"
   Back: "what?"
```

### 3. Add Helpful Examples
```
✅ Good: "I run every morning" → "Corro todas las mañanas"
❌ Bad: (no example)
```

### 4. Organize by Topic
```
✅ Good: Separate topics for different categories
❌ Bad: Everything in one "General" topic
```

### 5. Test Small Before Bulk
```
✅ Good: Import 5 test cards first
❌ Bad: Import 1000 cards, discover format issue
```

---

## Troubleshooting

### Cards Not Appearing?
- Check if they were created: Go to Cards page and use filter
- Verify user_id is 1 (default for all methods)
- Check console for errors

### Topic Not Created?
- Topics are auto-created by all methods
- Check spelling (case-sensitive)
- Verify in Topics page

### CSV Import Failed?
- Validate CSV format (use --create-sample)
- Check file encoding (should be UTF-8)
- Look for error messages in output

### Performance Issues?
- For >1000 cards, use bulk methods (not UI)
- Consider batching imports
- Database will auto-optimize

---

## Quick Reference

### Create Single Card (UI)
```
1. /cards → New Card → Fill form → Create
```

### Create Single Card (Script)
```python
from scripts.add_flashcard import add_flashcard
add_flashcard("Hello", "Hola", "Spanish")
```

### Import CSV
```bash
python scripts/import_csv.py my_cards.csv
```

### Create Sample CSV
```bash
python scripts/import_csv.py --create-sample
```

---

## Summary

You have **4 working methods** to add flashcards:

1. ✅ **Web UI** - `/cards` page (easiest for end users)
2. ✅ **Python Script** - `scripts/add_flashcard.py` (best for bulk)
3. ✅ **CSV Import** - `scripts/import_csv.py` (best for spreadsheets)
4. ✅ **Direct Database** - SQLModel code (advanced users)

Plus **1 future method**:
5. ⏳ **REST API** - Not yet implemented

All methods create proper flashcards with Leitner states, ready for review!

---

**Happy Flashcard Creation! 🎴**
