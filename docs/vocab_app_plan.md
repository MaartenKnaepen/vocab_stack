# Vocabulary Learning App - Implementation Plan

## Overview
A web-based spaced repetition learning application for memorizing word pairs (e.g., foreign language translations, verb conjugations, past-present tense). Built with Python-only stack, optimized for single-user deployment with proper architecture for potential multi-user expansion.

## Tech Stack
- **Framework**: Reflex (full-stack Python framework with built-in FastAPI)
- **Database**: SQLite (sufficient for single-user, easy backup)
- **Algorithm**: Leitner Box System (5 boxes with progressive intervals)
- **Deployment**: Online-only (Railway, Render, or similar)
- **Testing**: Pytest for core logic (spaced repetition algorithm, data models)

## Design Principles
- ✅ Reflex only (no separate FastAPI backend)
- ✅ Online-only (no offline PWA complexity for MVP)
- ✅ Single user initially, but properly structured database
- ✅ Simple CSV import (2 columns: question, answer)
- ✅ Topic-based filtering and organization
- ✅ Strategic testing (core logic only, not UI)

## Core Features (MVP)
1. CSV import with topic inference from filename
2. Leitner box spaced repetition system
3. Study sessions filtered by topic
4. Type-to-answer with auto-compare (override possible)
5. Progress tracking per topic and overall
6. Mobile-responsive interface

## Leitner Box System Specification

### Box Structure
- **Box 1**: Review daily (new cards + failed cards)
- **Box 2**: Review every 2 days
- **Box 3**: Review every 7 days (weekly)
- **Box 4**: Review every 14 days (bi-weekly)
- **Box 5**: Review every 30 days (monthly - mastered)

### Progression Rules
- ✅ **Correct answer**: Card moves to next box (Box 5 stays in Box 5)
- ❌ **Incorrect answer**: Card moves back to Box 1
- **Due date calculation**: Next review = last_reviewed + box_interval

### Study Session Logic
1. User selects topic to study
2. System shows all cards due today from that topic (across all boxes)
3. User types answer, system compares (fuzzy match)
4. User can override if comparison is wrong
5. Card moves to appropriate box based on result

## Data Model

### Tables

#### `users`
```
- id: INTEGER PRIMARY KEY
- username: TEXT UNIQUE NOT NULL
- created_at: TIMESTAMP DEFAULT CURRENT_TIMESTAMP
```
*Note: Hardcoded single user initially, but structured for expansion*

#### `topics`
```
- id: INTEGER PRIMARY KEY
- name: TEXT UNIQUE NOT NULL (e.g., "German Verbs", "Spanish Food")
- created_at: TIMESTAMP DEFAULT CURRENT_TIMESTAMP
- card_count: INTEGER DEFAULT 0 (computed)
```

#### `cards`
```
- id: INTEGER PRIMARY KEY
- topic_id: INTEGER FK -> topics.id
- question: TEXT NOT NULL
- answer: TEXT NOT NULL
- created_at: TIMESTAMP DEFAULT CURRENT_TIMESTAMP
```

#### `card_progress`
```
- id: INTEGER PRIMARY KEY
- card_id: INTEGER FK -> cards.id
- user_id: INTEGER FK -> users.id
- current_box: INTEGER DEFAULT 1 (1-5)
- last_reviewed: TIMESTAMP NULL
- next_review_date: DATE NOT NULL
- total_reviews: INTEGER DEFAULT 0
- correct_count: INTEGER DEFAULT 0
- incorrect_count: INTEGER DEFAULT 0
```

#### `review_history`
```
- id: INTEGER PRIMARY KEY
- card_progress_id: INTEGER FK -> card_progress.id
- reviewed_at: TIMESTAMP DEFAULT CURRENT_TIMESTAMP
- was_correct: BOOLEAN NOT NULL
- previous_box: INTEGER NOT NULL
- new_box: INTEGER NOT NULL
- user_answer: TEXT NULL (what user typed)
```

### Key Design Decisions

**Why separate `cards` and `card_progress`?**
- Cards are immutable content (question/answer pairs)
- Progress is user-specific state (box, review dates)
- Allows future multi-user expansion without duplicating cards

**Why `review_history` table?**
- Enables analytics (success rate trends over time)
- Audit trail for debugging algorithm
- Can show user their learning curve

**Topic assignment:**
- Inferred from CSV filename (e.g., `german_verbs.csv` → "German Verbs")
- User can manually edit topic names in UI
- Can reassign cards to different topics

## Application Architecture

### Reflex State Structure

#### `AppState` (Base state)
```
- current_user_id: int
- authenticated: bool (placeholder for future)
```

#### `ImportState` (CSV import)
```
- uploaded_file: bytes
- filename: str
- preview_data: List[tuple]
- topic_name: str (editable, auto-filled from filename)
- import_status: str
- error_message: str
```

#### `StudyState` (Study session)
```
- selected_topic_id: int
- current_card: Card
- user_answer: str
- show_result: bool
- is_correct: bool
- can_override: bool
- due_cards_remaining: int
- session_stats: dict (correct/incorrect for this session)
```

#### `ProgressState` (Dashboard/stats)
```
- topics: List[TopicStats]
- overall_stats: dict
- cards_due_today: int
- cards_due_by_topic: dict
```

### File Structure
```
vocab_stack/
├── vocab_app/
│   ├── __init__.py
│   ├── app.py                 # Main Reflex app entry point
│   ├── config.py              # Configuration (DB path, constants)
│   │
│   ├── models/
│   │   ├── __init__.py
│   │   ├── database.py        # SQLAlchemy engine setup
│   │   ├── user.py            # User model
│   │   ├── topic.py           # Topic model
│   │   ├── card.py            # Card model
│   │   ├── card_progress.py   # CardProgress model
│   │   └── review_history.py  # ReviewHistory model
│   │
│   ├── services/
│   │   ├── __init__.py
│   │   ├── import_service.py  # CSV parsing and import logic
│   │   ├── leitner_service.py # Leitner algorithm implementation
│   │   ├── study_service.py   # Study session logic
│   │   └── stats_service.py   # Statistics calculation
│   │
│   ├── utils/
│   │   ├── __init__.py
│   │   ├── text_comparison.py # Fuzzy matching for answers
│   │   └── date_helpers.py    # Date calculation utilities
│   │
│   ├── pages/
│   │   ├── __init__.py
│   │   ├── index.py           # Home/dashboard
│   │   ├── import_page.py     # CSV import interface
│   │   ├── study_page.py      # Study session interface
│   │   ├── topics_page.py     # Topic management
│   │   └── stats_page.py      # Statistics and progress
│   │
│   └── components/
│       ├── __init__.py
│       ├── navigation.py      # Nav bar component
│       ├── card_display.py    # Flashcard display component
│       └── progress_bar.py    # Progress visualization
│
├── tests/
│   ├── __init__.py
│   ├── test_leitner_service.py     # Core algorithm tests
│   ├── test_import_service.py      # CSV parsing tests
│   ├── test_text_comparison.py     # Answer matching tests
│   └── test_models.py              # Database model tests
│
├── data/
│   └── vocab.db              # SQLite database (gitignored)
│
├── assets/                   # Reflex assets (CSS, images)
├── .gitignore
├── pyproject.toml
├── README.md
└── alembic/                  # Database migrations (if needed)
```

## Implementation Phases

### Phase 1: Project Setup & Data Models (3-4 hours)
**Goal**: Database schema and models working

- [ ] Initialize Reflex project structure
- [ ] Set up SQLAlchemy models (all 5 tables)
- [ ] Create database initialization script
- [ ] Write migration to create tables
- [ ] Seed database with default user
- [ ] Test database CRUD operations

**Deliverable**: Working database with all tables, can create/read records via Python shell

---

### Phase 2: Leitner Algorithm Implementation (4-5 hours)
**Goal**: Core spaced repetition logic working and tested

- [ ] Implement `leitner_service.py`:
  - [ ] `get_due_cards(topic_id, user_id)` → returns cards due today
  - [ ] `process_review(card_id, was_correct)` → updates box and dates
  - [ ] `calculate_next_review_date(box_number, last_reviewed)` → date logic
- [ ] Write comprehensive tests for Leitner logic:
  - [ ] Card moves from Box 1→2 on correct
  - [ ] Card moves from Box 3→1 on incorrect
  - [ ] Box 5 stays in Box 5 on correct
  - [ ] Next review dates calculated correctly for each box
  - [ ] Due cards query returns correct cards for today
- [ ] Implement `date_helpers.py` for date calculations

**Deliverable**: Fully tested Leitner system passing all test cases

---

### Phase 3: CSV Import Functionality (3-4 hours)
**Goal**: Can import CSV files and create cards with topics

- [ ] Implement `import_service.py`:
  - [ ] Parse CSV (handle encoding issues, validate 2 columns)
  - [ ] Extract topic from filename (clean, titlecase)
  - [ ] Create topic if not exists
  - [ ] Bulk insert cards
  - [ ] Initialize card_progress for new cards (Box 1, due today)
- [ ] Write tests for import logic:
  - [ ] Valid CSV imports correctly
  - [ ] Invalid CSV raises appropriate errors
  - [ ] Topic extraction from filename works
  - [ ] Duplicate cards are handled gracefully
- [ ] Create `ImportState` and basic import page UI (Reflex)
- [ ] File upload component with preview

**Deliverable**: Working CSV import via UI, cards visible in database

---

### Phase 4: Study Session Interface (6-8 hours)
**Goal**: Can study cards with type-to-answer, updates progress

- [ ] Implement `study_service.py`:
  - [ ] Get next due card for topic
  - [ ] Validate user answer
  - [ ] Update card progress after review
  - [ ] Track session statistics
- [ ] Implement `text_comparison.py`:
  - [ ] Fuzzy string matching (handle typos, case, whitespace)
  - [ ] Configurable strictness (e.g., 85% similarity threshold)
  - [ ] Write tests for various answer scenarios
- [ ] Create `StudyState` and study page UI:
  - [ ] Topic selection dropdown
  - [ ] Card display (question prominently shown)
  - [ ] Answer input field
  - [ ] Submit button
  - [ ] Result display (correct/incorrect with expected answer)
  - [ ] Override buttons ("Mark Correct" / "Mark Incorrect")
  - [ ] Session progress (X/Y cards completed today)
  - [ ] Next card button

**Deliverable**: Functional study session where cards progress through boxes

---

### Phase 5: Dashboard & Statistics (4-5 hours)
**Goal**: User can see progress and choose topics to study

- [ ] Implement `stats_service.py`:
  - [ ] Get cards due today (total and by topic)
  - [ ] Calculate success rates (overall and by topic)
  - [ ] Get box distribution (how many cards in each box)
  - [ ] Get recent activity (last 7 days review count)
- [ ] Create `ProgressState` and dashboard page:
  - [ ] Cards due today (prominent display)
  - [ ] Topic list with due counts per topic
  - [ ] "Study Now" buttons per topic
  - [ ] Overall statistics cards
  - [ ] Box distribution visualization
  - [ ] Success rate trends
- [ ] Create topics management page:
  - [ ] List all topics
  - [ ] Edit topic names
  - [ ] View card count per topic
  - [ ] Delete topics (with confirmation)

**Deliverable**: Dashboard showing progress, easy navigation to study sessions

---

### Phase 6: Polish & UX Improvements (3-4 hours)
**Goal**: App feels smooth and professional

- [ ] Mobile-responsive design (test on phone)
- [ ] Loading states for all async operations
- [ ] Error handling with user-friendly messages
- [ ] Empty states (no cards due, no topics yet)
- [ ] Success animations/feedback for correct answers
- [ ] Keyboard shortcuts (Enter to submit, etc.)
- [ ] Navigation bar with active page indicator
- [ ] Consistent styling and color scheme
- [ ] Add basic instructions/help text

**Deliverable**: Polished, mobile-friendly UI

---

### Phase 7: Deployment (4-6 hours)
**Goal**: App running in production, accessible from phone

- [ ] Set up deployment platform (Railway/Render/Fly.io)
- [ ] Configure environment variables
- [ ] Set up persistent volume for SQLite database
- [ ] Configure Reflex for production mode
- [ ] Deploy and test
- [ ] Set up database backup strategy (simple script to download SQLite file)
- [ ] Document deployment process
- [ ] Test on actual mobile device (iPhone)
- [ ] Fix any deployment-specific issues

**Deliverable**: Live app accessible via URL, working on mobile

---

### Phase 8: Testing & Bug Fixes (2-3 hours)
**Goal**: Core functionality is reliable

- [ ] Manual testing of complete user flows:
  - [ ] Import CSV → Study → Check progress
  - [ ] Multiple study sessions with same cards
  - [ ] Edge cases (empty topics, all cards mastered)
- [ ] Fix any bugs discovered
- [ ] Performance testing (large datasets, 1000+ cards)
- [ ] Cross-browser testing (Chrome, Safari on iOS)

**Deliverable**: Stable, tested application

---

## Total Estimated Time: 29-39 hours

## Answer Validation Logic

### Fuzzy Matching Algorithm
Use `difflib.SequenceMatcher` or `fuzzywuzzy` library:

1. **Preprocessing**:
   - Convert both answers to lowercase
   - Strip leading/trailing whitespace
   - Remove common punctuation (configurable)

2. **Comparison**:
   - Calculate similarity ratio (0.0 to 1.0)
   - Threshold: ≥ 0.85 = correct, < 0.85 = incorrect

3. **Special Cases**:
   - Exact match = always correct
   - User can override any auto-judgment
   - Log user overrides for algorithm improvement

### Override Workflow
```
User types answer → Auto-compare → Show result
                                    ↓
                    [Result is X] - Did we get it wrong?
                                    ↓
                    [Mark as Correct] [Mark as Incorrect]
```

## CSV Import Specification

### File Format
```csv
question,answer
Hund,dog
Katze,cat
Haus,house
```

### Import Process
1. User uploads CSV file (e.g., `german_nouns.csv`)
2. System extracts topic name: "German Nouns" (from filename)
3. Preview shows first 5 rows
4. User can edit topic name
5. User clicks "Import"
6. System:
   - Creates topic if not exists
   - Creates cards linked to topic
   - Creates card_progress records (Box 1, due today)
7. Confirmation: "Imported 50 cards into topic 'German Nouns'"

### Error Handling
- Invalid CSV format → show error, don't import
- Missing columns → show error
- Duplicate cards → skip or merge (user choice)
- Empty cells → skip row, log warning

## Mobile-Responsive Design Guidelines

### Key Screens (Mobile-First)
1. **Dashboard**: Large "Study Now" buttons per topic, cards due prominently displayed
2. **Study Session**: Full-screen flashcard, large text, easy touch targets
3. **Import**: Simple file picker, minimal form fields

### Touch Interactions
- Large buttons (min 44x44px touch targets)
- Swipe gestures optional (nice-to-have, not MVP)
- No hover states (design for touch)

### Performance
- Minimize Reflex state updates (batch when possible)
- Lazy load statistics (only when viewing stats page)
- Keep study session fast (<100ms card transitions)

## Testing Strategy

### Unit Tests (Pytest)
Focus on core business logic:

1. **`test_leitner_service.py`** (CRITICAL)
   - Box transitions for all scenarios
   - Date calculations
   - Due card queries
   - Edge cases (new cards, mastered cards)

2. **`test_import_service.py`**
   - CSV parsing (valid/invalid formats)
   - Topic extraction from filenames
   - Duplicate handling

3. **`test_text_comparison.py`**
   - Answer matching accuracy
   - Edge cases (empty strings, special characters)
   - Similarity threshold behavior

4. **`test_models.py`**
   - Database constraints (foreign keys, unique constraints)
   - Relationship loading (cards → progress → history)

### Integration Tests (Optional, if time permits)
- End-to-end import → study → progress flow

### Manual Testing Checklist
- [ ] Import CSV with various formats
- [ ] Study session with correct/incorrect answers
- [ ] Card progression through all 5 boxes
- [ ] Statistics update after study sessions
- [ ] Mobile responsiveness on actual device
- [ ] Multiple topics management

## Future Enhancements (Post-MVP)

### Phase 9+ (Not in initial scope)
- [ ] **Multi-user authentication** (login/signup)
- [ ] **Bidirectional cards** (auto-create reverse pairs)
- [ ] **Manual card creation** (add cards via UI, not just CSV)
- [ ] **Edit/delete cards** (individual card management)
- [ ] **Audio support** (pronunciation, TTS)
- [ ] **Image support** (picture flashcards)
- [ ] **Export functionality** (backup as CSV/JSON)
- [ ] **Advanced statistics** (learning curve graphs, heatmaps)
- [ ] **Configurable Leitner intervals** (customize box schedules)
- [ ] **Gamification** (streaks, daily goals, achievements)
- [ ] **Shared decks** (import from community)
- [ ] **Offline PWA** (service workers, cache cards)
- [ ] **Spaced repetition alternatives** (SM-2, FSRS algorithms)

## Configuration Constants

### `config.py`
```python
# Database
DATABASE_URL = "sqlite:///data/vocab.db"

# Leitner box intervals (days)
BOX_INTERVALS = {
    1: 1,    # Daily
    2: 2,    # Every 2 days
    3: 7,    # Weekly
    4: 14,   # Bi-weekly
    5: 30,   # Monthly
}

# Answer validation
ANSWER_SIMILARITY_THRESHOLD = 0.85

# Study session
CARDS_PER_SESSION_DEFAULT = 20  # Suggested limit per topic

# Import
MAX_CSV_SIZE_MB = 5
ALLOWED_EXTENSIONS = [".csv", ".txt"]
```

## Deployment Considerations

### Platform Recommendations
1. **Railway**: Easy Reflex deployment, persistent volumes, $5/month
2. **Render**: Free tier available, good for demos
3. **Fly.io**: Good performance, global CDN

### Database Backup Strategy
- SQLite file is single file: `data/vocab.db`
- Automated backup: cron job to copy file to cloud storage
- Manual backup: download via admin endpoint
- Consider switching to PostgreSQL if scaling beyond single user

### Environment Variables
```
DATABASE_URL=sqlite:///data/vocab.db
REFLEX_ENV=production
REFLEX_BACKEND_PORT=8000
REFLEX_FRONTEND_PORT=3000
```

## Success Metrics

### MVP Launch Criteria
- [ ] Can import CSV with word pairs
- [ ] Can study cards with type-to-answer
- [ ] Cards progress through Leitner boxes correctly
- [ ] Dashboard shows due cards and stats
- [ ] Works on iPhone mobile browser
- [ ] All core algorithm tests passing
- [ ] Deployed and accessible via public URL

### User Experience Goals
- Study session feels fast and smooth
- Answer validation is accurate (>90% auto-correct)
- Mobile interface is comfortable for daily use
- Data persists reliably (no lost progress)

---

## Next Steps
1. Review and approve this plan
2. Begin Phase 1 implementation
3. Iterate with user feedback after each phase
