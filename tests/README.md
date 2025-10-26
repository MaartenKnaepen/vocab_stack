# Vocab Stack Test Suite

Comprehensive integration and unit tests for the Vocab Stack application.

## Test Files

### Integration Tests

#### 1. `test_authentication.py` - Authentication & Authorization
Tests user registration, login, password hashing, session management, and admin flags.

**Key Tests:**
- User registration with duplicate prevention
- Password hashing and verification
- Login with correct/incorrect credentials
- Session token validation
- Admin flag management
- Logout functionality

#### 2. `test_review_sessions.py` - Review Session Logic
Tests the core review functionality including card loading, filtering, and progress tracking.

**Key Tests:**
- Get all due cards for a user
- Filter cards by topic (shared topic feature)
- Due date filtering (only cards due today)
- Review with correct/incorrect answers
- Random review order
- Cards per session limit
- User data isolation in reviews
- Shared topic review (all users can review all cards in a topic)

#### 3. `test_topic_operations.py` - Topic CRUD & Cascade Deletion
Tests topic creation, card management, and cascade deletion ensuring data integrity.

**Key Tests:**
- Create topics
- Add flashcards to topics
- Cascade deletion (topic → flashcards → Leitner states → review history)
- Topic deletion isolation (doesn't affect other topics)
- Empty topic deletion

#### 4. `test_data_isolation.py` - Multi-User Data Separation
Tests that user data is properly isolated in a multi-user environment.

**Key Tests:**
- Users see only their own cards (without topic filter)
- Users see all cards in shared topics
- Review history is per-user
- Leitner state is shared per card
- Statistics are per-user
- Card ownership is tracked correctly
- Deleting user doesn't affect shared topics

#### 5. `test_admin_functions.py` - Admin Dashboard Operations
Tests admin-specific functionality for user management.

**Key Tests:**
- Admin flag set correctly
- Grant/revoke admin privileges
- Reset user passwords
- Delete user with all data (cascade)
- View all users
- View user statistics
- Prevent admin self-deletion

### Unit Tests

#### 6. `test_leitner_algorithm.py` - Leitner Spaced Repetition
Tests the Leitner algorithm for spaced repetition learning.

**Key Tests:**
- Box progression on correct answers
- Box reset on incorrect answers
- Next review date calculation
- Box 5 cards (mastered)
- Multiple reviews
- Due card filtering

### Other Tests

#### 7. `test_database.py` - Database CRUD Operations
Basic database operations and relationship testing.

#### 8. `test_complete_workflow.py` - End-to-End Workflows
Complete user workflows from registration to review.

## Running Tests

### Run All Tests
```bash
python tests/run_all_tests.py
```

### Run Individual Test Suites
```bash
python tests/test_authentication.py
python tests/test_review_sessions.py
python tests/test_topic_operations.py
python tests/test_data_isolation.py
python tests/test_admin_functions.py
python tests/test_leitner_algorithm.py
```

### Run Existing Tests
```bash
python tests/test_database.py
python tests/test_complete_workflow.py
```

## Test Coverage

### ✅ Covered Areas

**Authentication & Security:**
- User registration and login
- Password hashing
- Session management
- Admin access control

**Core Learning System:**
- Leitner algorithm (spaced repetition)
- Review sessions
- Progress tracking
- Due card filtering

**Data Management:**
- Topic operations
- Flashcard CRUD
- Cascade deletion
- Data integrity

**Multi-User Features:**
- User data isolation
- Shared topics
- Per-user statistics
- Per-user review history

**Admin Features:**
- User management
- Password reset
- Admin privileges
- User deletion

### ⚠️ Not Covered (UI/Frontend)
- Button clicks and UI interactions
- Page rendering
- CSS/styling
- Navigation flows (protected by middleware, but not tested)

### ⚠️ Not Covered (Advanced)
- Concurrent user sessions
- Rate limiting
- Session expiration edge cases
- Large dataset performance
- Database migrations

## Test Philosophy

### Integration Tests
Focus on **realistic workflows** and **data integrity**:
- Test full user journeys
- Verify database state after operations
- Ensure multi-user scenarios work correctly
- Check cascade operations don't leave orphaned data

### Unit Tests
Focus on **individual algorithms** and **business logic**:
- Leitner algorithm calculations
- Text comparison logic
- Date calculations
- Statistical computations

## Expected Results

All tests should pass with the current implementation. If any tests fail, it indicates:

1. **Regression** - Something broke that was working before
2. **Bug** - An existing bug that was discovered by the tests
3. **Data Issue** - Test database needs to be reset

## Test Database

Tests use a **separate test database** and:
- Reset the database before each test suite (`drop_all_tables()` + `create_db_and_tables()`)
- Create fresh test data for each test
- Don't affect your production/development database

## Adding New Tests

When adding new features, add tests to the appropriate file:

1. **Authentication features** → `test_authentication.py`
2. **Review logic** → `test_review_sessions.py`
3. **Topic management** → `test_topic_operations.py`
4. **Multi-user features** → `test_data_isolation.py`
5. **Admin features** → `test_admin_functions.py`
6. **Algorithm changes** → `test_leitner_algorithm.py`

Or create a new test file for entirely new features.

## Continuous Integration

These tests can be integrated into CI/CD pipelines:

```bash
# Run tests and exit with appropriate code
python tests/run_all_tests.py
# Exit code 0 = all passed, 1 = some failed
```

## Troubleshooting

### Tests are failing
1. Check if database is locked (close any running app instances)
2. Ensure all dependencies are installed (`pip install -r requirements.txt`)
3. Check if test database path is correct
4. Review error messages carefully

### Tests are slow
- Each test suite resets the database (intentional for isolation)
- Consider running individual test files instead of all tests
- Database operations are the main bottleneck

### Import errors
Make sure you're running from the project root directory:
```bash
cd /path/to/vocab_stack
python tests/run_all_tests.py
```

## Test Metrics

Total test suites: **6**
Total test cases: **~50+**
Test coverage: **Core functionality ~90%**

## Next Steps

After all tests pass:
1. ✅ Core functionality is verified
2. ✅ Multi-user scenarios work correctly
3. ✅ Data integrity is maintained
4. ✅ Admin features are secure
5. 🚀 Ready for deployment preparation
