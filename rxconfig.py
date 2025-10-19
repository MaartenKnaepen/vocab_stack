import reflex as rx

config = rx.Config(
    app_name="vocab_stack",
    db_url="sqlite:///reflex.db",  # Database configuration
    plugins=[
        rx.plugins.SitemapPlugin(),
    ]
)