import reflex as rx
import os
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

config = rx.Config(
    app_name="vocab_stack",
    db_url=os.getenv("DATABASE_URL"),  # Database configuration
    backend_host="0.0.0.0",  # Bind to all interfaces for deployment
    backend_port=8000,  # Fixed port for Docker
    api_url=os.getenv("API_URL", "http://localhost:3000"),  # Use env var for flexibility
    deploy_url=os.getenv("DEPLOY_URL", "http://localhost:3000"),  # Use env var for flexibility
    plugins=[
        rx.plugins.SitemapPlugin(),
    ]
)   