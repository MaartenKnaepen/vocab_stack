"""Initialize database with all tables."""
import sys
sys.path.insert(0, '.')

from vocab_stack.database import create_db_and_tables

if __name__ == "__main__":
    print("Creating database tables...")
    create_db_and_tables()
    print("Done!")
