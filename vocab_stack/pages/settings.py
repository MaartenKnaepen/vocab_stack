"""Settings and preferences page."""
import reflex as rx
from vocab_stack.services.settings_service import SettingsService
from vocab_stack.pages.auth import AuthState


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
    answer_mode: str = "reveal"
    
    # UI state
    loading: bool = False
    success_message: str = ""
    error_message: str = ""
    
    async def on_mount(self):
        """Load settings on page mount."""
        await self.load_settings()
    
    async def load_settings(self):
        """Load user settings."""
        # Page is already protected by auth middleware, so user must be logged in
        auth = await self.get_state(AuthState)
        if not auth.current_user_id:
            return
            
        self.loading = True
        
        # Use current user's ID
        user_id = auth.current_user_id
        settings = SettingsService.get_user_settings(user_id)
        
        self.username = settings.get("username", auth.username)
        self.email = settings.get("email", "")
        self.cards_per_session = settings.get("cards_per_session", 20)
        self.review_order = settings.get("review_order", "random")
        self.show_examples = settings.get("show_examples", True)
        self.theme = settings.get("theme", "light")
        self.daily_goal = settings.get("daily_goal", 50)
        self.answer_mode = settings.get("answer_mode", "reveal")
        
        self.loading = False
    
    async def save_preferences(self):
        """Save user preferences."""
        # Page is already protected by auth middleware
        auth = await self.get_state(AuthState)
        if not auth.current_user_id:
            return
            
        settings = {
            "cards_per_session": self.cards_per_session,
            "review_order": self.review_order,
            "show_examples": self.show_examples,
            "theme": self.theme,
            "daily_goal": self.daily_goal,
            "answer_mode": self.answer_mode,
        }
        
        success = SettingsService.update_user_settings(auth.current_user_id, settings)
        
        if success:
            self.success_message = "Preferences saved successfully!"
            self.error_message = ""
        else:
            self.error_message = "Failed to save preferences"
            self.success_message = ""
    
    async def save_profile(self):
        """Save profile information."""
        # Page is already protected by auth middleware
        auth = await self.get_state(AuthState)
        if not auth.current_user_id:
            return
            
        success, message = SettingsService.update_profile(
            auth.current_user_id,
            username=self.username,
            email=self.email
        )
        
        if success:
            self.success_message = message
            self.error_message = ""
        else:
            self.error_message = message
            self.success_message = ""
    
    def update_cards_per_session(self, value: list[float]):
        """Update cards per session from slider (receives list)."""
        if value:
            self.cards_per_session = int(value[0])
    
    def update_daily_goal(self, value: list[float]):
        """Update daily goal from slider (receives list)."""
        if value:
            self.daily_goal = int(value[0])


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
                        default_value=SettingsState.cards_per_session,
                        on_value_commit=SettingsState.update_cards_per_session,
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
                        default_value=SettingsState.daily_goal,
                        on_value_commit=SettingsState.update_daily_goal,
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
            rx.vstack(
                rx.text("Answer Mode", weight="bold", size="2"),
                rx.select(
                    ["reveal", "type"],
                    value=SettingsState.answer_mode,
                    on_change=SettingsState.set_answer_mode,
                    width="200px",
                ),
                rx.text(
                    rx.cond(
                        SettingsState.answer_mode == "reveal",
                        "Click to reveal answer (easier)",
                        "Type answer for automatic checking (harder)"
                    ),
                    size="1",
                    color="gray"
                ),
                spacing="1",
                align="start",
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
            SettingsState.success_message.to_string() != "",
            rx.callout(
                SettingsState.success_message,
                icon="check",
                color_scheme="green",
            ),
        ),
        rx.cond(
            SettingsState.error_message.to_string() != "",
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
