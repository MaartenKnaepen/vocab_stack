"""Create admin user."""
import sys
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from vocab_stack.services.auth_service import AuthService

def create_admin():
    """Create admin user with default credentials."""
    print("Creating admin user...")
    
    # Register admin
    success, message, user = AuthService.register_user(
        username="admin",
        email="admin@vocab.com",
        password="admin123"  # CHANGE THIS AFTER FIRST LOGIN!
    )
    
    if success and user:
        # Promote to admin
        AuthService.promote_to_admin(user.id)
        print(f"✅ Admin user created successfully!")
        print(f"   Username: admin")
        print(f"   Email: admin@vocab.com")
        print(f"   Password: admin123")
        print()
        print("⚠️  IMPORTANT: Please change the password after first login!")
        print("   Go to Settings after logging in.")
    else:
        if "already" in message.lower():
            print(f"ℹ️  Admin user already exists: {message}")
            print("   If you need to reset, delete the user from database first.")
        else:
            print(f"❌ Error creating admin user: {message}")
        return False
    
    return True

if __name__ == "__main__":
    create_admin()
