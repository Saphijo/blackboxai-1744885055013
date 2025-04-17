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

# Check if X server is running
if ! command -v xset &> /dev/null; then
    echo -e "${RED}X server utilities not found. Installing...${NC}"
    sudo apt-get update && sudo apt-get install -y x11-xserver-utils
fi

# Get the current display
current_display=$(w -h | grep -m1 ":[0-9]" | grep -o ":[0-9]")
if [ -z "$current_display" ]; then
    current_display=":0"
fi

echo -e "${BLUE}Using display${NC} ${GREEN}$current_display${NC}"

# Activate virtual environment
echo -e "${BLUE}Activating virtual environment...${NC}"
. venv/bin/activate

# Set display environment variables
export DISPLAY=$current_display
export SDL_VIDEODRIVER=x11

echo -e "${GREEN}Starting Cocktail Interface...${NC}"
echo -e "${BLUE}Controls:${NC}"
echo -e "- Swipe left/right to browse cocktails"
echo -e "- Tap cocktail to start mixing"
echo -e "- Press ESC to exit"
echo -e "${BLUE}Press Ctrl+C to stop${NC}"

# Run the interface
python3 cocktail_interface.py
