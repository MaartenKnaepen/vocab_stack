"""Main application setup and routes."""
import reflex as rx
from vocab_stack.components.navigation import layout
from vocab_stack.pages.dashboard import dashboard_page, DashboardState
from vocab_stack.pages.review import review_page, ReviewState
from vocab_stack.pages.topics import topics_page, TopicState
from vocab_stack.pages.cards import cards_page, CardState
from vocab_stack.pages.statistics import statistics_page, StatsState
from vocab_stack.pages.settings import settings_page, SettingsState
from vocab_stack.pages.auth import login_page, register_page, AuthState
from vocab_stack.pages.admin import register_admin_routes


# Authentication middleware to protect routes
def require_auth(page):
    """Middleware to require authentication for a page."""
    def protected_page():
        return rx.cond(
            AuthState.is_logged_in,
            page(),
            rx.vstack(
                rx.heading("Please log in to continue", size="9", mb=6),
                rx.text("You need to sign in to access this page."),
                rx.link("Go to login", href="/", size="4", color="blue.500"),
                width="100%",
                height="80vh",
                align="center",
                justify="center",
            )
        )
    return protected_page


# Use default theme (per-user theme can be implemented with client-side storage)
user_theme = "light"

# Define the app with authentication middleware
app = rx.App(
    theme=rx.theme(
        appearance=user_theme,
        accent_color="blue",
        radius="large",
    )
)

# Authentication routes (available to all users)
app.add_page(
    login_page,
    route="/",
    title="Login - Vocab App"
)

app.add_page(
    register_page,
    route="/register",
    title="Register - Vocab App"
)

# Protected routes (require authentication)
app.add_page(
    lambda: layout(require_auth(dashboard_page)()),
    route="/dashboard",
    title="Dashboard - Vocab App",
    on_load=DashboardState.on_mount,
)

app.add_page(
    lambda: layout(require_auth(review_page)()),
    route="/review",
    title="Review - Vocab App",
    on_load=ReviewState.on_mount,
)

app.add_page(
    lambda: layout(require_auth(topics_page)()),
    route="/topics",
    title="Topics - Vocab App",
    on_load=TopicState.on_mount,
)

app.add_page(
    lambda: layout(require_auth(cards_page)()),
    route="/cards",
    title="Flashcards - Vocab App",
    on_load=CardState.on_mount,
)

app.add_page(
    lambda: layout(require_auth(statistics_page)()),
    route="/statistics",
    title="Statistics - Vocab App",
    on_load=StatsState.on_mount,
)

app.add_page(
    lambda: layout(require_auth(settings_page)()),
    route="/settings",
    title="Settings - Vocab App",
    on_load=SettingsState.on_mount,
)

# Register admin routes
register_admin_routes(app)
