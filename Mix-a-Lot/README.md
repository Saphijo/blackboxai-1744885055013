# Raspberry Pi 5 Pump Testing Interface

A web-based interface for testing and controlling pumps on a Raspberry Pi 5. This interface allows individual pump testing, GPIO pin configuration, and provides safety features for pump control.

## Requirements

- Raspberry Pi 5
- Python 3.7 or higher (pre-installed on Raspberry Pi OS)
- pip3
- Internet connection (for initial setup)
- GPIO access (automatically switches to simulation mode if not available)

### Package Versions

The application uses specific versions of packages tested on Raspberry Pi:

```
Flask==3.0.0
gpiozero==2.0
RPi.GPIO==0.7.1
Werkzeug==3.0.1
```

These versions are specified in requirements.txt and will be installed automatically during setup. Do not manually upgrade these packages as it may cause compatibility issues with the Raspberry Pi.

## Quick Start

1. Verify Python Installation:
```bash
# Check Python version
python3 --version

# Check pip3 installation
pip3 --version

# If pip3 is not installed:
sudo apt update
sudo apt install -y python3-pip
```

2. Install required system packages:
```bash
sudo apt update
sudo apt install -y python3-venv git
```

3. Setup and run the application:
```bash
# Copy all files to a directory
mkdir pump-test
cp -r Mix-a-Lot/* pump-test/
cd pump-test

# Make scripts executable
chmod +x setup.sh run.sh

# Run setup
./setup.sh

# Start the application
./run.sh
```

5. Access the interface:
```
http://<raspberry-pi-ip>:8000
```

## Features

- Individual pump testing (Forward/Backward)
- GPIO and Direction pin swapping
- Emergency stop functionality
- Real-time status updates
- Automatic simulation mode for development
- Clean virtual environment setup

## Configuration

Pump configuration is stored in `pumpen.json`:
```json
{
  "pumps": [
    {
      "id": 1,
      "gpio_pin": 17,
      "direction_pin": 27,
      "assigned_liquid": "Rum",
      "calibration": {
        "ml_per_second": 1.5
      }
    },
    ...
  ]
}
```

## Troubleshooting

### Common Issues

1. If configuration file not found:
```bash
# Make sure you're running the application from the correct directory
pwd  # Should show you're in the pump-test directory
ls   # Should show pumpen.json in the current directory

# If pumpen.json is missing, copy it from the source
cp ../Mix-a-Lot/pumpen.json .
```

2. If setup.sh reports Python not found:
```bash
# Verify Python installation
which python3
python3 --version

# If needed, create symlink
sudo ln -s $(which python3) /usr/local/bin/python3
```

2. If pip3 is not found:
```bash
# Install pip3
sudo apt update
sudo apt install -y python3-pip

# Verify installation
pip3 --version
```

3. If venv creation fails:
```bash
# Install venv module
sudo apt install -y python3-venv

# Clear any failed venv
rm -rf venv

# Try setup again
./setup.sh
```

### GPIO Issues

1. If GPIO access fails:
   - Ensure you're running as a user with GPIO permissions
   - Add your user to the gpio group:
     ```bash
     sudo usermod -a -G gpio $USER
     # Log out and back in for changes to take effect
     ```
   - Reboot the Pi if needed

2. If the web interface is not accessible:
   - Check if port 8000 is in use:
     ```bash
     sudo lsof -i :8000
     # If needed, kill the process
     sudo kill <PID>
     ```
   - Verify network connection
   - Check firewall settings:
     ```bash
     sudo ufw status
     # If needed, allow port 8000
     sudo ufw allow 8000
     ```

## Safety Features

- All GPIO pins are cleared after each test
- Emergency stop button for immediate shutdown
- Pin state validation before operations
- Automatic GPIO cleanup on shutdown

## Development vs Production

- Development: Runs in simulation mode when GPIO is not available
- Production: Uses real GPIO when running on Raspberry Pi
- Clear visual indication of current mode in the interface

## Stopping the Application

1. Use the Emergency Stop button in the interface
2. Press Ctrl+C in the terminal
3. All GPIO pins will be automatically cleaned up

## Support

For issues or questions:
1. Check the troubleshooting section
2. Verify your Python and pip installation
3. Check GPIO permissions
4. Contact system administrator

## Security Notes

- Change default passwords
- Keep system and packages updated
- Restrict network access as needed
- Use SSL/TLS for production deployments
