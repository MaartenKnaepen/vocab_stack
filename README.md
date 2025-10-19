# Vocabulary Learning App 🎴

A full-stack vocabulary learning application with spaced repetition using the Leitner system, built with Python and Reflex.

## Features

- 🎴 **Flashcard Management** - Create, edit, and organize flashcards by topic
- 📊 **Leitner Spaced Repetition** - Intelligent scheduling based on performance
- 📈 **Statistics & Progress Tracking** - Comprehensive analytics and insights
- ⚙️ **Customizable Settings** - Personalize your learning experience
- 🎯 **Daily Goals** - Track and achieve daily review targets
- 📱 **Responsive Design** - Works on desktop and mobile
- 🌙 **Dark Mode** - Light and dark theme support

## Tech Stack

- **Framework**: [Reflex](https://reflex.dev/) (Python full-stack)
- **Database**: SQLite (SQLAlchemy/SQLModel)
- **Migrations**: Alembic
- **Language**: Python 3.13+

## Installation

### Prerequisites

- Python 3.13 or higher
- pip or uv package manager

### Setup

```bash
# Clone the repository
git clone <repository-url>
cd vocab_stack

# Create virtual environment
python -m venv .venv
source .venv/bin/activate  # On Windows: .venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt
# OR using uv
uv pip install -r requirements.txt

# Initialize database with migrations
alembic upgrade head

# Seed database with sample data (optional)
python scripts/seed_data.py

# Run development server
reflex run
```

The app will be available at `http://localhost:3000`

## Usage

### Quick Start

1. **Dashboard** - View your topics and cards due for review
2. **Review** - Study flashcards with intelligent spaced repetition
3. **Topics** - Organize your flashcards into topics
4. **Cards** - Manage individual flashcards
5. **Statistics** - Track your learning progress
6. **Settings** - Customize your experience

### Creating Your First Flashcard

1. Go to **Topics** and create a new topic (e.g., "Spanish Vocabulary")
2. Go to **Cards** and click "New Card"
3. Fill in:
   - **Front**: The question or word (e.g., "Hello")
   - **Back**: The answer or translation (e.g., "Hola")
   - **Example**: Optional example sentence
   - **Topic**: Select the topic you created
4. Click "Create"

### Reviewing Flashcards

1. Go to **Dashboard** to see cards due for review
2. Click "Start Review" or "Review Now" on a specific topic
3. Study the question, then click "Show Answer"
4. Rate yourself:
   - ✅ **Correct** - Card moves to next box (longer interval)
   - ❌ **Incorrect** - Card returns to Box 1 (review sooner)
5. Continue until session is complete

### Customizing Settings

Go to **Settings** to adjust:
- **Cards per Session**: How many cards to review at once (5-100)
- **Review Order**: Random, oldest first, or newest first
- **Daily Goal**: Target number of reviews per day (10-200)
- **Show Examples**: Toggle example sentences during review
- **Theme**: Light or dark mode (requires app restart)

## Project Structure

```
vocab_stack/
├── components/          # Reusable UI components
│   ├── navigation.py    # Navbar and layout
│   └── notifications.py # Toast notifications
├── models.py            # Database models
├── pages/               # Page components
│   ├── dashboard.py     # Main dashboard
│   ├── review.py        # Review session
│   ├── topics.py        # Topic management
│   ├── cards.py         # Card management
│   ├── statistics.py    # Progress tracking
│   └── settings.py      # User settings
├── services/            # Business logic
│   ├── leitner_service.py      # Spaced repetition algorithm
│   ├── statistics_service.py   # Analytics calculations
│   └── settings_service.py     # Settings management
├── utils/               # Utility functions
│   ├── date_helpers.py         # Date calculations
│   └── error_handlers.py       # Error handling utilities
├── database.py          # Database configuration
└── app.py              # Main app configuration

alembic/                 # Database migrations
├── versions/            # Migration files
└── env.py              # Migration configuration

tests/                   # Test suite
├── test_database.py
├── test_leitner_algorithm.py
└── test_complete_workflow.py

docs/                    # Documentation
├── phase1-7.md          # Implementation guides
├── reflex_reactive_patterns.md
└── settings_*.md        # Settings documentation
```

## Running Tests

```bash
# Run database tests
python tests/test_database.py

# Run Leitner algorithm tests
python tests/test_leitner_algorithm.py

# Run complete workflow tests
python tests/test_complete_workflow.py

# Run all tests
python tests/test_database.py && \
python tests/test_leitner_algorithm.py && \
python tests/test_complete_workflow.py
```

## Database Migrations

```bash
# Create a new migration
alembic revision --autogenerate -m "description"

# Apply migrations
alembic upgrade head

# Rollback one migration
alembic downgrade -1

# View current version
alembic current

# View migration history
alembic history
```

## Development

### Adding a New Feature

1. Create/update models in `vocab_stack/models.py`
2. Generate migration: `alembic revision --autogenerate -m "feature name"`
3. Apply migration: `alembic upgrade head`
4. Add service logic in `vocab_stack/services/`
5. Create UI in `vocab_stack/pages/`
6. Add route in `vocab_stack/app.py`
7. Add tests in `tests/`

### Reflex Reactive Patterns

When working with Reflex, follow these patterns to avoid reactive Var issues:

- ✅ **DO**: Precompute booleans in state methods
- ✅ **DO**: Use `.to_string()` for string concatenation
- ✅ **DO**: Create simple lists for rendering
- ❌ **DON'T**: Use Python comparisons on reactive Vars at render time
- ❌ **DON'T**: Use f-strings with reactive Vars
- ❌ **DON'T**: Iterate over reactive Vars with list comprehensions

See `docs/reflex_reactive_patterns.md` for comprehensive guide.

## Features by Phase

### Phase 1-3: Core System ✅
- Database models and relationships
- Leitner spaced repetition algorithm
- Dashboard with topic overview
- Review sessions with flashcards

### Phase 4: Management ✅
- Topic CRUD operations
- Flashcard CRUD operations
- Card statistics display

### Phase 5: Analytics ✅
- User statistics overview
- Box distribution charts
- Review history tracking
- Topic performance analysis
- Learning streak tracking

### Phase 6: Settings ✅
- User profile management
- Review preferences (cards per session, order)
- Daily goal setting
- Theme selection
- Show/hide examples toggle

### Phase 7: Polish ✅
- Error handling and validation
- Comprehensive testing
- Loading states
- Documentation
- Production ready

## Contributing

Contributions are welcome! Please:

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add/update tests
5. Submit a pull request

## License

MIT License - see LICENSE file for details

## Support

For issues, questions, or suggestions:
- Open an issue on GitHub
- Check the documentation in `docs/`
- Review the implementation guides

## Acknowledgments

- Built with [Reflex](https://reflex.dev/)
- Implements the [Leitner System](https://en.wikipedia.org/wiki/Leitner_system)
- Inspired by spaced repetition apps like Anki

---

**Happy Learning! 🎓**
