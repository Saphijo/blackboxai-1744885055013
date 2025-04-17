#!/bin/bash

# Colors for output
GREEN='\033[0;32m'
BLUE='\033[0;34m'
RED='\033[0;31m'
NC='\033[0m' # No Color

# Check if virtual environment exists
if [ ! -d "venv" ]; then
    echo -e "${RED}Virtual environment not found. Please run setup.sh first.${NC}"
    exit 1
fi

# Activate virtual environment
echo -e "${BLUE}Activating virtual environment...${NC}"
. venv/bin/activate


# Run the application
echo -e "${GREEN}Starting Pump Testing Interface...${NC}"
echo -e "${BLUE}Access the interface at:${NC}"
echo -e "${GREEN}http://localhost:8000${NC}"
echo -e "${BLUE}Press Ctrl+C to stop the server${NC}"
python3 app.py
