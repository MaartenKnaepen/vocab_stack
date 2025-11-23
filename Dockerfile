# Use Python 3.11 slim image
FROM python:3.11-slim

# Set working directory
WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    curl \
    build-essential \
    libpq-dev \
    unzip \
    && rm -rf /var/lib/apt/lists/*

# Copy dependency files first
COPY pyproject.toml uv.lock* ./

# Install Python dependencies using pip
RUN pip install --no-cache-dir -e .

# Copy application code
COPY . .

# Create necessary directories
RUN mkdir -p /app/.web /app/uploaded_files /app/backups

# Expose port
EXPOSE 8000

# Run database migrations and start the app
# Create tables using SQLModel (bypassing Alembic since migrations are inconsistent)
# Important: Import models first so SQLModel knows about them
CMD ["sh", "-c", "python -c 'from vocab_stack import models; from vocab_stack.database import create_db_and_tables; create_db_and_tables()' && python scripts/create_admin.py && reflex run --env prod"]
