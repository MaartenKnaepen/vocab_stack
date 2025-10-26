# Running Tests with Pytest

## Quick Start

```bash
# Run all tests
pytest

# Run specific test file
pytest tests/test_authentication.py

# Run with verbose output
pytest -v

# Run and show print statements
pytest -s

# Run specific test
pytest tests/test_authentication.py::TestAuthentication::test_user_registration

# Run and stop at first failure
pytest -x

# Run tests in parallel (if pytest-xdist installed)
pytest -n auto
```

## Current Status

⚠️ **Tests need to be updated to match actual AuthService API**

The test files were created with placeholder API calls that don't match the actual implementation.

**Actual AuthService methods:**
- `register_user(username, email, password)` → returns `(bool, str, Optional[User])`
- `login_user(username, password)` → returns `(bool, str, Optional[User])`
- `hash_password(password)` → returns `str`
- `verify_password(password, hash)` → returns `bool`
- `validate_token(token)` → returns `Optional[User]`
- `logout(user_id)` → returns `None`

**Test files need updates:**
- ✅ `test_leitner_algorithm.py` - Should work (already exists)
- ❌ `test_authentication.py` - Needs API updates
- ❌ `test_review_sessions.py` - Needs API updates
- ❌ `test_topic_operations.py` - Needs API updates
- ❌ `test_data_isolation.py` - Needs API updates
- ❌ `test_admin_functions.py` - Needs API updates

## Recommendation

Since the tests revealed API mismatches, you have two options:

**Option A: Update tests to match current API**
- Faster, tests the actual code
- I can do this quickly

**Option B: Keep manual test runners**
- Current tests work as standalone scripts
- Just run: `python tests/test_authentication.py`

**Which would you prefer?**
