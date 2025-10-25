"""Settings and preferences service."""
import reflex as rx
from vocab_stack.models import User
from sqlmodel import select


class SettingsService:
    """Service for managing user settings."""
    
    @staticmethod
    def get_user_settings(user_id: int) -> dict:
        """Get user settings."""
        with rx.session() as session:
            user = session.get(User, user_id)
            if not user:
                return {}
            
            return {
                "username": user.username,
                "email": user.email,
                "cards_per_session": user.cards_per_session,
                "review_order": user.review_order,
                "show_examples": user.show_examples,
                "theme": user.theme,
                "daily_goal": user.daily_goal,
                "answer_mode": user.answer_mode,
            }
    
    @staticmethod
    def update_user_settings(user_id: int, settings: dict) -> bool:
        """Update user settings."""
        try:
            with rx.session() as session:
                user = session.get(User, user_id)
                if not user:
                    return False
                
                # Update fields
                if "cards_per_session" in settings:
                    user.cards_per_session = settings["cards_per_session"]
                
                if "review_order" in settings:
                    user.review_order = settings["review_order"]
                
                if "show_examples" in settings:
                    user.show_examples = settings["show_examples"]
                
                if "theme" in settings:
                    user.theme = settings["theme"]
                
                if "daily_goal" in settings:
                    user.daily_goal = settings["daily_goal"]
                
                if "answer_mode" in settings:
                    user.answer_mode = settings["answer_mode"]
                
                session.add(user)
                session.commit()
                return True
        except Exception as e:
            print(f"Error updating settings: {e}")
            return False
    
    @staticmethod
    def update_profile(user_id: int, username: str = None, email: str = None) -> tuple[bool, str]:
        """Update user profile information."""
        with rx.session() as session:
            user = session.get(User, user_id)
            if not user:
                return False, "User not found"
            
            # Check for duplicate username
            if username and username != user.username:
                existing = session.exec(
                    select(User).where(User.username == username)
                ).first()
                if existing:
                    return False, "Username already taken"
                user.username = username
            
            # Check for duplicate email
            if email and email != user.email:
                existing = session.exec(
                    select(User).where(User.email == email)
                ).first()
                if existing:
                    return False, "Email already in use"
                user.email = email
            
            session.add(user)
            session.commit()
            return True, "Profile updated successfully"
