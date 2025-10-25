#!/usr/bin/env python3
"""Make mknaepen an admin user."""

import sys
sys.path.insert(0, '.')

from vocab_stack.database import get_session
from vocab_stack.models import User
from sqlmodel import select

print("Making mknaepen an admin...\n")

with get_session() as session:
    # Find the user
    user = session.exec(select(User).where(User.username == "mknaepen")).first()
    
    if not user:
        print("❌ User 'mknaepen' not found!")
        sys.exit(1)
    
    # Check if already admin
    if user.is_admin:
        print(f"✓ User '{user.username}' is already an admin")
    else:
        # Make admin
        user.is_admin = True
        session.add(user)
        session.commit()
        print(f"✅ User '{user.username}' is now an admin!")
    
    print(f"\nUser details:")
    print(f"  - Username: {user.username}")
    print(f"  - Email: {user.email}")
    print(f"  - User ID: {user.id}")
    print(f"  - Admin: {user.is_admin}")
    print(f"\n🎉 You can now access the admin dashboard at: /admin")
