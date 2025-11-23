#!/bin/bash

# Color codes
GREEN='\033[0;32m'
BLUE='\033[0;34m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
NC='\033[0m'

echo -e "${BLUE}🔍 Testing Vocab Stack Setup...${NC}\n"

# Check if .env exists
if [ -f .env ]; then
    echo -e "${GREEN}✅ .env file exists${NC}"
else
    echo -e "${RED}❌ .env file not found${NC}"
    echo -e "${YELLOW}   Run: cp .env.local.example .env${NC}"
    exit 1
fi

# Check if passwords are still default
if grep -q "CHANGE_THIS" .env; then
    echo -e "${RED}❌ Default passwords detected in .env${NC}"
    echo -e "${YELLOW}   Please edit .env and set DB_PASSWORD and SECRET_KEY${NC}"
    exit 1
else
    echo -e "${GREEN}✅ .env file configured${NC}"
fi

# Check if Docker is installed
if command -v docker &> /dev/null; then
    echo -e "${GREEN}✅ Docker is installed${NC}"
else
    echo -e "${RED}❌ Docker not found${NC}"
    exit 1
fi

# Check if Docker daemon is running
if docker ps &> /dev/null; then
    echo -e "${GREEN}✅ Docker daemon is running${NC}"
else
    echo -e "${RED}❌ Docker daemon not running${NC}"
    exit 1
fi

# Check if containers are running
if docker ps | grep -q vocab_stack_app; then
    echo -e "${GREEN}✅ Vocab Stack app is running${NC}"
    echo -e "${BLUE}   Access at: http://localhost:8000${NC}"
else
    echo -e "${YELLOW}⚠️  Vocab Stack not running yet${NC}"
    echo -e "${BLUE}   Run: ./start.sh${NC}"
fi

echo -e "\n${GREEN}✅ Setup check complete!${NC}"
