import reflex as rx
import os

config = rx.Config(
    app_name="vocab_stack",
    db_url=os.getenv("DATABASE_URL"),  # Database configuration
    plugins=[
        rx.plugins.SitemapPlugin(),
    ]
)   