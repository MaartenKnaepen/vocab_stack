#!/usr/bin/env python3
"""Initialize database - create tables if they don't exist, then run migrations."""

import sys
import os
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

def init_database():
    """Create all tables if they don't exist."""
    print("🔧 Initializing database...")
    
    # Import after path is set
    from sqlmodel import SQLModel
    from vocab_stack.database import engine
    import vocab_stack.models  # Import to register all models
    
    print(f"📍 Database location: {engine.url}")
    
    # Ensure the database directory exists
    db_url = str(engine.url)
    if db_url.startswith('sqlite:///'):
        db_path = db_url.replace('sqlite:///', '')
        db_dir = os.path.dirname(db_path)
        if db_dir and not os.path.exists(db_dir):
            print(f"📁 Creating directory: {db_dir}")
            os.makedirs(db_dir, exist_ok=True)
    
    try:
        # Create all tables defined in SQLModel
        print("🔨 Creating database tables...")
        SQLModel.metadata.create_all(engine)
        print("✅ Database tables created/verified successfully!")
        return True
    except Exception as e:
        print(f"❌ Error creating tables: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = init_database()
    sys.exit(0 if success else 1)
