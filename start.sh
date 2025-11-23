#!/bin/bash

# Color codes for output
GREEN='\033[0;32m'
BLUE='\033[0;34m'
RED='\033[0;31m'
NC='\033[0m' # No Color

echo -e "${BLUE}🚀 Starting Vocab Stack...${NC}"

# Check if .env exists
if [ ! -f .env ]; then
    echo -e "${RED}❌ Error: .env file not found!${NC}"
    echo -e "${BLUE}Creating .env from .env.local.example...${NC}"
    cp .env.local.example .env
    echo -e "${RED}⚠️  Please edit .env and set your passwords and secret key!${NC}"
    echo -e "${BLUE}Then run this script again.${NC}"
    exit 1
fi

# Create backups directory if it doesn't exist
mkdir -p backups

# Start Docker containers
echo -e "${BLUE}📦 Building and starting containers...${NC}"
docker compose up -d --build

# Wait for containers to be healthy
echo -e "${BLUE}⏳ Waiting for services to be ready...${NC}"
sleep 5

# Check if containers are running
if docker ps | grep -q vocab_stack_app; then
    echo -e "${GREEN}✅ Vocab Stack is running!${NC}"
    echo -e "${BLUE}📍 Access the app at: http://localhost:8000${NC}"
    echo -e "${BLUE}📊 View logs: docker-compose logs -f${NC}"
else
    echo -e "${RED}❌ Failed to start containers${NC}"
    echo -e "${BLUE}Check logs: docker-compose logs${NC}"
    exit 1
fi
