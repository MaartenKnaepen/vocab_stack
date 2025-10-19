"""Main application setup and routes."""
import reflex as rx
from vocab_stack.components.navigation import layout
from vocab_stack.pages.dashboard import dashboard_page, DashboardState
from vocab_stack.pages.review import review_page, ReviewState
from vocab_stack.pages.topics import topics_page, TopicState
from vocab_stack.pages.cards import cards_page, CardState
from vocab_stack.pages.statistics import statistics_page, StatsState
from vocab_stack.pages.settings import settings_page, SettingsState


# Load user theme preference (default to light if not set)
def get_user_theme() -> str:
    """Get user's theme preference from database."""
    try:
        from vocab_stack.services.settings_service import SettingsService
        settings = SettingsService.get_user_settings(1)  # Hardcoded user_id for demo
        return settings.get("theme", "light")
    except Exception:
        # If database not initialized or error, default to light
        return "light"


user_theme = get_user_theme()

app = rx.App(
    theme=rx.theme(
        appearance=user_theme,  # "light" or "dark"
        accent_color="blue",
        radius="large",
    )
)

# Dashboard
app.add_page(
    lambda: layout(dashboard_page()),
    route="/",
    title="Dashboard - Vocab App",
    on_load=DashboardState.on_mount,
)

# Review
app.add_page(
    lambda: layout(review_page()),
    route="/review",
    title="Review - Vocab App",
    on_load=ReviewState.on_mount,
)

# Topics
app.add_page(
    lambda: layout(topics_page()),
    route="/topics",
    title="Topics - Vocab App",
    on_load=TopicState.on_mount,
)

# Cards
app.add_page(
    lambda: layout(cards_page()),
    route="/cards",
    title="Flashcards - Vocab App",
    on_load=CardState.on_mount,
)

# Statistics
app.add_page(
    lambda: layout(statistics_page()),
    route="/statistics",
    title="Statistics - Vocab App",
    on_load=StatsState.on_mount,
)

# Settings
app.add_page(
    lambda: layout(settings_page()),
    route="/settings",
    title="Settings - Vocab App",
    on_load=SettingsState.on_mount,
)
