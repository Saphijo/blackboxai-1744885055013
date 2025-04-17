#!/bin/bash

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

echo -e "${BLUE}Setting up Mix-a-Lot Interface...${NC}"

# Check if python3 is installed using 'which'
PYTHON3_PATH=$(which python3)
if [ -z "$PYTHON3_PATH" ]; then
    echo -e "${RED}Python 3 is not installed. Please install Python 3 first.${NC}"
    exit 1
else
    echo -e "${GREEN}Found Python 3 at: $PYTHON3_PATH${NC}"
fi

# Check if pip3 is installed using 'which'
PIP3_PATH=$(which pip3)
if [ -z "$PIP3_PATH" ]; then
    echo -e "${RED}pip3 is not installed. Please install pip3 first.${NC}"
    exit 1
else
    echo -e "${GREEN}Found pip3 at: $PIP3_PATH${NC}"
fi

# Create virtual environment if it doesn't exist
if [ ! -d "venv" ]; then
    echo -e "${BLUE}Creating virtual environment...${NC}"
    $PYTHON3_PATH -m venv venv
fi

# Activate virtual environment
echo -e "${BLUE}Activating virtual environment...${NC}"
. venv/bin/activate

# Check if running on Linux
if [ "$(uname)" != "Linux" ]; then
    echo -e "${RED}This application requires Linux (Raspberry Pi) to control GPIO pins.${NC}"
    exit 1
fi

# Check for and install system dependencies
echo -e "${BLUE}Checking for system dependencies...${NC}"
echo -e "${RED}Note: This requires sudo access. Please enter your password if prompted.${NC}"
sudo apt-get update
if ! dpkg -l | grep -q "liblgpio-dev"; then
    echo -e "${BLUE}Installing lgpio dependencies...${NC}"
    sudo apt-get install -y liblgpio-dev
fi
if ! dpkg -l | grep -q "python3-pygame"; then
    echo -e "${BLUE}Installing Pygame and display dependencies...${NC}"
    sudo apt-get install -y python3-pygame libsdl2-2.0-0 libsdl2-mixer-2.0-0 \
                           libsdl2-image-2.0-0 libsdl2-ttf-2.0-0 \
                           x11-xserver-utils xinit
fi

# Install Python requirements from requirements.txt
echo -e "${BLUE}Installing Python packages...${NC}"
pip install -r requirements.txt

# Make run scripts executable
echo -e "${BLUE}Making scripts executable...${NC}"
chmod +x run.sh run_cocktails.sh

# Set up autostart
echo -e "${BLUE}Setting up automatic startup...${NC}"

# Install systemd service
echo -e "${BLUE}Installing systemd service...${NC}"
sudo cp mix-a-lot.service /etc/systemd/system/
sudo systemctl daemon-reload
sudo systemctl enable mix-a-lot.service

# Install desktop entry
echo -e "${BLUE}Installing desktop entry...${NC}"
mkdir -p ~/.config/autostart
cp mix-a-lot.desktop ~/.config/autostart/
chmod +x ~/.config/autostart/mix-a-lot.desktop

# Configure display settings
echo -e "${BLUE}Configuring display settings...${NC}"
# Create or update config.txt to set screen orientation
if [ -f "/boot/config.txt" ]; then
    # Remove any existing display_rotate setting
    sudo sed -i '/^display_rotate=/d' /boot/config.txt
    # Add our display_rotate setting
    echo "display_rotate=1" | sudo tee -a /boot/config.txt
fi

# Deactivate virtual environment
deactivate

echo -e "${GREEN}Setup complete!${NC}"
echo -e "\n${BLUE}The Mix-a-Lot interface will now:${NC}"
echo -e "1. Start automatically on boot"
echo -e "2. Run in fullscreen mode"
echo -e "3. Display in vertical orientation"
echo -e "4. Restart automatically if it crashes"

echo -e "\n${BLUE}To start the interface manually:${NC}"
echo -e "1. Web Interface (Pump Testing):"
echo -e "   Run: ${GREEN}./run.sh${NC}"
echo -e "   Access at: ${GREEN}http://localhost:8000${NC}"

echo -e "\n2. Touch Screen Interface (Cocktail Mixing):"
echo -e "   Run: ${GREEN}./run_cocktails.sh${NC}"

echo -e "\n${BLUE}To stop either interface:${NC}"
echo -e "Press ${GREEN}Ctrl+C${NC}"

echo -e "\n${GREEN}Please reboot your Raspberry Pi for all changes to take effect.${NC}"
