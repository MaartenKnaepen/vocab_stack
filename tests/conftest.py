"""Pytest configuration and shared fixtures."""
import sys
import os
from pathlib import Path

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent))

# Set test database before importing anything else
# CRITICAL: Reflex uses REFLEX_DB_URL, not DATABASE_URL!
os.environ["REFLEX_DB_URL"] = "sqlite:///test_vocab_stack.db"

import pytest
from vocab_stack.database import create_db_and_tables, drop_all_tables


@pytest.fixture(scope="session", autouse=True)
def setup_test_environment():
    """Set up test environment once for all tests."""
    print("\n🧪 Using TEST database: test_vocab_stack.db")
    print("⚠️  Production database (vocab_stack.db) will NOT be affected")
    # This runs once before all tests
    yield
    # Cleanup after all tests


@pytest.fixture(scope="function")
def clean_database():
    """Provide a clean database for each test function."""
    drop_all_tables()
    create_db_and_tables()
    yield
    # Optionally clean up after test
    # drop_all_tables()
