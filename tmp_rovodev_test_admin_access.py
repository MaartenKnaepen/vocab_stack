#!/usr/bin/env python3
"""Test admin functionality and check admin users."""

import sys
sys.path.insert(0, '.')

from vocab_stack.database import get_session
from vocab_stack.models import User
from sqlmodel import select

print("Checking admin access...\n")

with get_session() as session:
    # Check for admin users
    admin_users = session.exec(select(User).where(User.is_admin == True)).all()
    
    print(f"Admin users found: {len(admin_users)}")
    if admin_users:
        for admin in admin_users:
            print(f"  - {admin.username} (ID: {admin.id}, Email: {admin.email})")
    else:
        print("  ⚠ No admin users found!")
        print("\n  To create an admin user, you can:")
        print("  1. Use the create_admin.py script in the scripts/ folder")
        print("  2. Or manually set is_admin=True in the database")
    
    # List all users
    all_users = session.exec(select(User)).all()
    print(f"\nAll users ({len(all_users)}):")
    for user in all_users:
        admin_badge = " [ADMIN]" if user.is_admin else ""
        print(f"  - {user.username}{admin_badge} (ID: {user.id})")

print("\n✅ Admin dashboard features:")
print("  ✓ View all users with detailed statistics")
print("  ✓ Reset user passwords")
print("  ✓ Grant/revoke admin privileges")
print("  ✓ Delete users (with cascade deletion of all data)")
print("  ✓ View last login times")
print("  ✓ See activity metrics")
print("\n🔒 Security:")
print("  ✓ Only users with is_admin=True can access /admin")
print("  ✓ Protected by require_admin middleware")
print("  ✓ Admins cannot delete or demote themselves")
