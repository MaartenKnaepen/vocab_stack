#!/bin/bash

# Color codes for output
GREEN='\033[0;32m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

echo -e "${BLUE}🛑 Stopping Vocab Stack...${NC}"

# Stop Docker containers
docker-compose down

echo -e "${GREEN}✅ Vocab Stack stopped${NC}"
echo -e "${BLUE}💡 To remove all data, run: docker-compose down -v${NC}"
