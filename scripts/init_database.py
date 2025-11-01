#!/usr/bin/env python3
"""Initialize database - create tables if they don't exist, then run migrations."""

import sys
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from vocab_stack.database import engine
from vocab_stack.models import SQLModel

def init_database():
    """Create all tables if they don't exist."""
    print("🔧 Initializing database...")
    print(f"📍 Database location: {engine.url}")
    
    try:
        # Create all tables defined in SQLModel
        SQLModel.metadata.create_all(engine)
        print("✅ Database tables created/verified")
        return True
    except Exception as e:
        print(f"❌ Error creating tables: {e}")
        return False

if __name__ == "__main__":
    success = init_database()
    sys.exit(0 if success else 1)
