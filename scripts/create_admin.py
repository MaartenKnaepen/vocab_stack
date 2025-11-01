#!/usr/bin/env python3
"""Script to create an admin user for the vocab app."""

import sys
import os
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from vocab_stack.services.auth_service import AuthService
from vocab_stack.database import get_session
from vocab_stack.models import User


def create_admin_user():
    """Create the default admin user if it doesn't exist."""
    # Get credentials from environment or use defaults
    admin_username = os.getenv("ADMIN_USERNAME", "admin")
    admin_email = os.getenv("ADMIN_EMAIL", "admin@vocab.com")
    admin_password = os.getenv("ADMIN_PASSWORD", "admin123")
    
    print(f"🔧 Checking for admin user '{admin_username}'...")
    
    try:
        with get_session() as session:
            # Check if admin already exists
            existing_admin = session.query(User).filter_by(username=admin_username).first()
            
            if existing_admin:
                print(f"✅ Admin user '{admin_username}' already exists.")
                if not existing_admin.is_admin:
                    print(f"   ℹ️  Promoting '{admin_username}' to admin...")
                    existing_admin.is_admin = True
                    session.commit()
                    print(f"   ✅ User promoted to admin!")
                return True
            
            # Create new admin user
            print(f"📝 Creating admin user '{admin_username}'...")
            success, message, user = AuthService.register_user(
                username=admin_username,
                email=admin_email,
                password=admin_password
            )
            
            if success and user:
                # Promote to admin
                print(f"🔐 Promoting user to admin...")
                AuthService.promote_to_admin(user.id)
                
                print(f"\n{'='*60}")
                print(f"✅ Admin user created successfully!")
                print(f"{'='*60}")
                print(f"  👤 Username: {admin_username}")
                print(f"  📧 Email:    {admin_email}")
                print(f"  🔑 Password: {admin_password}")
                print(f"{'='*60}")
                
                if admin_password == "admin123":
                    print(f"⚠️  SECURITY WARNING:")
                    print(f"   Using default password!")
                    print(f"   CHANGE IT IMMEDIATELY after first login!")
                    print(f"   Go to Settings → Change Password")
                    print(f"{'='*60}\n")
                
                return True
            else:
                print(f"❌ Failed to create admin user: {message}")
                return False
                
    except Exception as e:
        print(f"❌ Error creating admin user: {e}")
        import traceback
        traceback.print_exc()
        return False


if __name__ == "__main__":
    try:
        success = create_admin_user()
        sys.exit(0 if success else 1)
    except Exception as e:
        print(f"❌ Fatal error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
