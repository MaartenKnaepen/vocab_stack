# Phase 6: Settings & User Preferences - Implementation Guide

## Overview
This guide covers implementing user settings and preferences for customizing the learning experience.

**Estimated Time**: 2-3 hours  
**Goal**: Working settings page with user preferences and customization options

---

## Prerequisites

- ✅ Phase 5 completed (statistics working)
- ✅ Basic understanding of state persistence

---

## Step 1: Extend User Model (20 minutes)

Update `vocab_app/models.py` to add user preferences:

```python
class User(rx.Model, table=True):
    """User account information."""
    id: Optional[int] = Field(default=None, primary_key=True)
    username: str = Field(index=True, unique=True)
    email: str = Field(unique=True)
    created_at: datetime = Field(default_factory=datetime.utcnow)
    
    # Preferences
    cards_per_session: int = Field(default=20, ge=5, le=100)
    review_order: str = Field(default="random")  # random, oldest_first, newest_first
    show_examples: bool = Field(default=True)
    theme: str = Field(default="light")  # light, dark
    daily_goal: int = Field(default=50, ge=10, le=200)
    
    # Relationships
    flashcards: List["Flashcard"] = Relationship(back_populates="user")
```

After updating the model, create a migration:

```bash
reflex db makemigrations --message "Add user preferences"
reflex db migrate
```

---

## Step 2: Create Settings Service (30 minutes)

Create `vocab_app/services/settings_service.py`:

```python
"""Settings and preferences service."""
import reflex as rx
from vocab_app.models import User
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
```

---

## Step 3: Create Settings Page (60 minutes)

Create `vocab_app/pages/settings.py`:

```python
"""Settings and preferences page."""
import reflex as rx
from vocab_app.services.settings_service import SettingsService


class SettingsState(rx.State):
    """State for settings page."""
    
    # Profile
    username: str = ""
    email: str = ""
    
    # Preferences
    cards_per_session: int = 20
    review_order: str = "random"
    show_examples: bool = True
    theme: str = "light"
    daily_goal: int = 50
    
    # UI state
    loading: bool = False
    success_message: str = ""
    error_message: str = ""
    
    def on_mount(self):
        """Load settings on page mount."""
        self.load_settings()
    
    def load_settings(self):
        """Load user settings."""
        self.loading = True
        
        # User ID hardcoded to 1 for demo
        user_id = 1
        settings = SettingsService.get_user_settings(user_id)
        
        self.username = settings.get("username", "")
        self.email = settings.get("email", "")
        self.cards_per_session = settings.get("cards_per_session", 20)
        self.review_order = settings.get("review_order", "random")
        self.show_examples = settings.get("show_examples", True)
        self.theme = settings.get("theme", "light")
        self.daily_goal = settings.get("daily_goal", 50)
        
        self.loading = False
    
    def save_preferences(self):
        """Save user preferences."""
        settings = {
            "cards_per_session": self.cards_per_session,
            "review_order": self.review_order,
            "show_examples": self.show_examples,
            "theme": self.theme,
            "daily_goal": self.daily_goal,
        }
        
        success = SettingsService.update_user_settings(1, settings)
        
        if success:
            self.success_message = "Preferences saved successfully!"
            self.error_message = ""
        else:
            self.error_message = "Failed to save preferences"
            self.success_message = ""
    
    def save_profile(self):
        """Save profile information."""
        success, message = SettingsService.update_profile(
            1,
            username=self.username,
            email=self.email
        )
        
        if success:
            self.success_message = message
            self.error_message = ""
        else:
            self.error_message = message
            self.success_message = ""


def settings_section(title: str, content: rx.Component) -> rx.Component:
    """Render a settings section."""
    return rx.card(
        rx.vstack(
            rx.heading(title, size="5"),
            rx.divider(),
            content,
            spacing="4",
            align="start",
        ),
    )


def profile_section() -> rx.Component:
    """Profile settings section."""
    return settings_section(
        "Profile",
        rx.vstack(
            rx.vstack(
                rx.text("Username", weight="bold", size="2"),
                rx.input(
                    value=SettingsState.username,
                    on_change=SettingsState.set_username,
                    placeholder="Enter username",
                    width="100%",
                ),
                spacing="1",
                align="start",
            ),
            rx.vstack(
                rx.text("Email", weight="bold", size="2"),
                rx.input(
                    value=SettingsState.email,
                    on_change=SettingsState.set_email,
                    placeholder="Enter email",
                    type="email",
                    width="100%",
                ),
                spacing="1",
                align="start",
            ),
            rx.button(
                "Save Profile",
                on_click=SettingsState.save_profile,
                width="150px",
            ),
            spacing="3",
            align="start",
            width="100%",
        ),
    )


def review_preferences_section() -> rx.Component:
    """Review preferences section."""
    return settings_section(
        "Review Preferences",
        rx.vstack(
            rx.vstack(
                rx.text("Cards per Session", weight="bold", size="2"),
                rx.hstack(
                    rx.slider(
                        value=SettingsState.cards_per_session,
                        on_change=SettingsState.set_cards_per_session,
                        min=5,
                        max=100,
                        step=5,
                        width="300px",
                    ),
                    rx.text(SettingsState.cards_per_session.to_string(), weight="bold"),
                    spacing="3",
                ),
                spacing="1",
                align="start",
            ),
            rx.vstack(
                rx.text("Review Order", weight="bold", size="2"),
                rx.select(
                    ["random", "oldest_first", "newest_first"],
                    value=SettingsState.review_order,
                    on_change=SettingsState.set_review_order,
                    width="200px",
                ),
                spacing="1",
                align="start",
            ),
            rx.vstack(
                rx.text("Daily Goal (reviews)", weight="bold", size="2"),
                rx.hstack(
                    rx.slider(
                        value=SettingsState.daily_goal,
                        on_change=SettingsState.set_daily_goal,
                        min=10,
                        max=200,
                        step=10,
                        width="300px",
                    ),
                    rx.text(SettingsState.daily_goal.to_string(), weight="bold"),
                    spacing="3",
                ),
                spacing="1",
                align="start",
            ),
            rx.hstack(
                rx.switch(
                    checked=SettingsState.show_examples,
                    on_change=SettingsState.set_show_examples,
                ),
                rx.text("Show examples during review", size="2"),
                spacing="2",
            ),
            rx.button(
                "Save Preferences",
                on_click=SettingsState.save_preferences,
                width="150px",
            ),
            spacing="4",
            align="start",
            width="100%",
        ),
    )


def appearance_section() -> rx.Component:
    """Appearance preferences section."""
    return settings_section(
        "Appearance",
        rx.vstack(
            rx.vstack(
                rx.text("Theme", weight="bold", size="2"),
                rx.select(
                    ["light", "dark"],
                    value=SettingsState.theme,
                    on_change=SettingsState.set_theme,
                    width="200px",
                ),
                rx.text("Note: Theme will apply on next page load", size="1", color="gray"),
                spacing="1",
                align="start",
            ),
            spacing="3",
            align="start",
            width="100%",
        ),
    )


def settings_page() -> rx.Component:
    """Settings page content."""
    return rx.vstack(
        rx.heading("Settings", size="8"),
        
        # Success/Error messages
        rx.cond(
            SettingsState.success_message != "",
            rx.callout(
                SettingsState.success_message,
                icon="check",
                color_scheme="green",
            ),
        ),
        rx.cond(
            SettingsState.error_message != "",
            rx.callout(
                SettingsState.error_message,
                icon="triangle_alert",
                color_scheme="red",
            ),
        ),
        
        rx.cond(
            SettingsState.loading,
            rx.spinner(size="3"),
            rx.vstack(
                profile_section(),
                review_preferences_section(),
                appearance_section(),
                spacing="4",
                width="100%",
            ),
        ),
        
        spacing="6",
        width="100%",
        max_width="800px",
    )
```

---

## Step 4: Update Navigation and Routes (15 minutes)

Update `vocab_app/components/navigation.py`:

```python
def navbar() -> rx.Component:
    """Top navigation bar."""
    return rx.box(
        rx.hstack(
            rx.heading("🎴 Vocab App", size="7"),
            rx.spacer(),
            rx.hstack(
                rx.link(rx.button("Dashboard", variant="soft"), href="/"),
                rx.link(rx.button("Review", variant="soft"), href="/review"),
                rx.link(rx.button("Topics", variant="soft"), href="/topics"),
                rx.link(rx.button("Cards", variant="soft"), href="/cards"),
                rx.link(rx.button("Statistics", variant="soft"), href="/statistics"),
                rx.link(rx.button("Settings", variant="soft"), href="/settings"),  # NEW
                spacing="3",
            ),
            width="100%",
            padding="1rem",
            align="center",
        ),
        background="var(--accent-3)",
        position="sticky",
        top="0",
        z_index="1000",
        border_bottom="1px solid var(--gray-6)",
    )
```

Update `vocab_app/app.py`:

```python
from vocab_app.pages.settings import settings_page, SettingsState

# Add settings page
app.add_page(
    lambda: layout(settings_page()),
    route="/settings",
    title="Settings - Vocab App",
    on_load=SettingsState.on_mount,
)
```

---

## Step 5: Apply User Preferences (30 minutes)

Update `vocab_app/pages/review.py` to use user preferences:

```python
class ReviewState(rx.State):
    """State for flashcard review."""
    
    # Add user preferences
    cards_per_session: int = 20
    show_examples: bool = True
    
    def on_mount(self):
        """Load cards when page loads."""
        # Load user preferences first
        self.load_user_preferences()
        self.load_review_cards()
    
    def load_user_preferences(self):
        """Load user preferences."""
        from vocab_app.services.settings_service import SettingsService
        settings = SettingsService.get_user_settings(1)
        self.cards_per_session = settings.get("cards_per_session", 20)
        self.show_examples = settings.get("show_examples", True)
    
    def load_review_cards(self, topic_id: int = None):
        """Load cards due for review."""
        self.loading = True
        
        # Get due cards (limited by cards_per_session)
        all_cards = LeitnerService.get_due_cards(
            topic_id=topic_id,
            user_id=1
        )
        
        # Limit to cards_per_session
        self.cards_to_review = all_cards[:self.cards_per_session]
        
        # Rest of the method...
```

Update flashcard display to respect show_examples:

```python
def flashcard_display() -> rx.Component:
    """Display the current flashcard."""
    return rx.card(
        rx.cond(
            ReviewState.show_answer == False,
            # Front of card
            rx.vstack(
                rx.text("Question", size="2", color="gray", weight="bold"),
                rx.heading(
                    ReviewState.current_card["front"],
                    size="8",
                    text_align="center",
                ),
                rx.button(
                    "Show Answer",
                    on_click=ReviewState.flip_card,
                    size="3",
                    variant="soft",
                ),
                spacing="4",
                align="center",
            ),
            # Back of card
            rx.vstack(
                rx.text("Answer", size="2", color="gray", weight="bold"),
                rx.heading(
                    ReviewState.current_card["back"],
                    size="7",
                    text_align="center",
                ),
                # Conditionally show example based on preference
                rx.cond(
                    ReviewState.show_examples & (ReviewState.current_card["example"] != ""),
                    rx.box(
                        rx.text("Example:", size="2", color="gray", weight="bold"),
                        rx.text(
                            ReviewState.current_card["example"],
                            size="3",
                            style={"font-style": "italic"},
                        ),
                        padding="1rem",
                        background="var(--gray-3)",
                        border_radius="0.5rem",
                    ),
                ),
                rx.hstack(
                    rx.button(
                        "❌ Incorrect",
                        on_click=ReviewState.mark_incorrect,
                        size="3",
                        color_scheme="red",
                        width="150px",
                    ),
                    rx.button(
                        "✅ Correct",
                        on_click=ReviewState.mark_correct,
                        size="3",
                        color_scheme="green",
                        width="150px",
                    ),
                    spacing="4",
                ),
                spacing="4",
                align="center",
            ),
        ),
        width="100%",
        max_width="600px",
        min_height="400px",
        padding="3rem",
    )
```

---

## Verification Checklist

- [ ] Settings page loads correctly
- [ ] Can update username and email
- [ ] Can change cards per session (5-100)
- [ ] Can select review order
- [ ] Can toggle show examples
- [ ] Can set daily goal (10-200)
- [ ] Can change theme preference
- [ ] Success/error messages display
- [ ] Review page respects preferences
- [ ] Changes persist after page reload

---

## Next Steps

**Ready for Phase 7**: Polish & Testing

---

**Phase 6 Complete!** 🎉
