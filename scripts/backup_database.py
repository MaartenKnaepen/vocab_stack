#!/usr/bin/env python3
"""Backup the database."""
import sys
import shutil
from datetime import datetime
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

# Backup SQLite database
db_path = Path("vocab_stack.db")
if db_path.exists():
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    backup_path = Path(f"vocab_stack_backup_{timestamp}.db")
    shutil.copy2(db_path, backup_path)
    print(f"✅ Database backed up to: {backup_path}")
else:
    print("❌ Database file not found: vocab_stack.db")
    sys.exit(1)
