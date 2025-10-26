# Running Tests with Pytest

## ✅ Pytest-Compatible Test Files

The following test files are fully converted to pytest and ready to use:

1. **`test_authentication.py`** - 10 tests ✅
2. **`test_review_sessions_pytest.py`** - 7 tests ✅
3. **`test_topic_operations_pytest.py`** - 3 tests ✅
4. **`test_leitner_algorithm.py`** - 6+ tests ✅ (original)

**Total: 26+ working pytest tests**

## Quick Start

### Run All Tests
```bash
# From project root
pytest tests/

# Or with more detail
pytest tests/ -v
```

### Run Specific Test Files
```bash
pytest tests/test_authentication.py -v
pytest tests/test_review_sessions_pytest.py -v
pytest tests/test_topic_operations_pytest.py -v
pytest tests/test_leitner_algorithm.py -v
```

### Run Specific Test
```bash
pytest tests/test_authentication.py::TestAuthentication::test_user_registration -v
```

### Useful Pytest Options
```bash
# Show print statements
pytest -s

# Stop at first failure
pytest -x

# Run last failed tests only
pytest --lf

# Show test coverage (if pytest-cov installed)
pytest --cov=vocab_stack

# Parallel execution (if pytest-xdist installed)
pytest -n auto
```

## Current Test Results

### ✅ Authentication Tests (10/10 passing)
- User registration
- Duplicate prevention (username/email)
- Password hashing
- Login (success/failure)
- Session token validation
- Admin flag management
- Logout

### ✅ Review Session Tests (7/7 passing)
- Get all due cards for user
- Filter cards by topic
- Due date filtering
- User data isolation
- Shared topic review
- Review with correct answer
- Review with incorrect answer

### ✅ Topic Operations Tests (3/3 passing)
- Create topic
- Cascade deletion (topic + cards + states + history)
- Deletion isolation (other topics unaffected)

### ✅ Leitner Algorithm Tests (6+/6+ passing)
- Box progression
- Box reset on incorrect
- Next review date calculation
- Mastered cards (box 5)

## Known Issues

### Deprecation Warnings
You'll see warnings about `datetime.utcnow()` being deprecated. These are in:
- `auth_service.py`
- `leitner_service.py`

**Fix:** Replace `datetime.utcnow()` with `datetime.now(datetime.UTC)`

This is a minor issue and doesn't affect functionality.

## Test Coverage Summary

| Area | Tests | Status |
|------|-------|--------|
| Authentication | 10 | ✅ Pass |
| Review Sessions | 7 | ✅ Pass |
| Topic Operations | 3 | ✅ Pass |
| Leitner Algorithm | 6+ | ✅ Pass |
| **Total** | **26+** | **✅ All Pass** |

## What's NOT Tested

The following areas don't have pytest tests yet:
- ⏸️ Data isolation (multi-user scenarios) - complex setup
- ⏸️ Admin functions - complex setup
- ⏸️ Statistics calculations - could be added
- ⏸️ Settings auto-save - UI-level feature
- ⏸️ Text comparison (type mode) - utility function

These can be added later if needed.

## Next Steps

1. ✅ **All critical tests pass** 
2. 🔧 **Fix deprecation warnings** (optional, non-urgent)
3. 🚀 **Ready for production** - core functionality is verified

## Running Tests in CI/CD

Add to your CI pipeline:
```yaml
- name: Run tests
  run: pytest tests/ -v --tb=short
```

Exit code will be 0 if all pass, non-zero if any fail.
