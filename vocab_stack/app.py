"""Main application setup and routes."""
import reflex as rx
from vocab_stack.components.navigation import layout
from vocab_stack.pages.dashboard import dashboard_page, DashboardState
from vocab_stack.pages.review import review_page, ReviewState


app = rx.App(
    theme=rx.theme(
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
