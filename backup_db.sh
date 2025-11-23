#!/bin/bash

# Load environment variables
if [ -f .env ]; then
    export $(cat .env | grep -v '^#' | xargs)
fi

# Set defaults if not in .env
DB_USER=${DB_USER:-vocabuser}
DB_NAME=${DB_NAME:-vocab_stack_db}

# Backup file path (overwrites each time)
BACKUP_FILE="./backups/vocab_db_backup.sql"

# Create backups directory if it doesn't exist
mkdir -p ./backups

# Color codes
GREEN='\033[0;32m'
BLUE='\033[0;34m'
RED='\033[0;31m'
NC='\033[0m'

echo -e "${BLUE}📦 Starting database backup...${NC}"

# Perform backup using docker exec
docker exec vocab_stack_db pg_dump -U "$DB_USER" "$DB_NAME" > "$BACKUP_FILE"

# Check if backup was successful
if [ $? -eq 0 ]; then
    BACKUP_SIZE=$(du -h "$BACKUP_FILE" | cut -f1)
    echo -e "${GREEN}✅ Backup completed successfully!${NC}"
    echo -e "${BLUE}📁 Location: $BACKUP_FILE${NC}"
    echo -e "${BLUE}📊 Size: $BACKUP_SIZE${NC}"
    echo -e "${BLUE}🕐 Timestamp: $(date '+%Y-%m-%d %H:%M:%S')${NC}"
else
    echo -e "${RED}❌ Backup failed!${NC}"
    exit 1
fi
