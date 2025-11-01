import reflex as rx
import os

config = rx.Config(
    app_name="vocab_stack",
    db_url=os.getenv("DATABASE_URL"),  # Database configuration
    backend_host="0.0.0.0",  # Bind to all interfaces for deployment
    backend_port=int(os.getenv("PORT", "8000")),  # Use PORT env var from Render
    api_url=f"https://vocab-stack.onrender.com",  # Production API URL
    deploy_url=f"https://vocab-stack.onrender.com",  # Production deploy URL
    plugins=[
        rx.plugins.SitemapPlugin(),
    ]
)   