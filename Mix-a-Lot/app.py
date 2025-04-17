from flask import Flask, render_template, request, jsonify
import json
import time
import sys
from gpiozero import DigitalOutputDevice, GPIOZeroError, Device
from gpiozero.pins.lgpio import LGPIOFactory

# Set lgpio as the default pin factory
Device.pin_factory = LGPIOFactory()

app = Flask(__name__)

# Constants
CONFIG_FILE = 'pumpen.json'  # Path to JSON configuration file
TEST_DURATION_SECONDS = 1.0  # Duration for each direction (forward/backward)
DELAY_BETWEEN_DIRECTIONS = 0.5 # Short pause between direction changes
DELAY_BETWEEN_PUMPS = 1.0      # Pause between testing different pumps
FORWARD_LEVEL = 0    # Level for forward direction
BACKWARD_LEVEL = 1   # Level for backward direction

# Global variable for initialized devices
pump_gpio_devices = {}

def load_config(filename):
    """Load pump configuration from a JSON file."""
    try:
        with open(filename, 'r') as f:
            config = json.load(f)
        if 'pumps' not in config or not isinstance(config['pumps'], list):
            print(f"Error: '{filename}' does not contain a valid 'pumps' array.")
            return None  # Signal an error
        return config['pumps']
    except FileNotFoundError:
        print(f"Error: Configuration file '{filename}' not found.")
        return None
    except json.JSONDecodeError:
        print(f"Error: Configuration file '{filename}' is not valid JSON.")
        return None
    except Exception as e:
        print(f"An unexpected error occurred while loading the configuration: {e}")
        return None

def setup_pump_gpio(pump_config):
    """Initialize GPIO devices for a pump. Returns (power_pin, direction_pin) on success, else (None, None)."""
    try:
        print(f"- Initializing Pump {pump_config.get('id')} (Power: GPIO{pump_config.get('gpio_pin')}, Direction: GPIO{pump_config.get('direction_pin')})")
        power_pin = DigitalOutputDevice(pump_config['gpio_pin'], initial_value=False)
        direction_pin = DigitalOutputDevice(pump_config['direction_pin'], initial_value=False)
        return power_pin, direction_pin
    except GPIOZeroError as e:
        print(f"  ! GPIO error initializing for Pump {pump_config.get('id')} "
              f"(Pins: {pump_config.get('gpio_pin')}, {pump_config.get('direction_pin')}): {e}")
        return None, None
    except KeyError as e:
        print(f"  ! Error: Missing key '{e}' in configuration for Pump {pump_config.get('id')}.")
        return None, None
    except Exception as e:
        print(f"  ! Unexpected error initializing Pump {pump_config.get('id')}: {e}")
        return None, None

def run_forward(power_pin, direction_pin, duration):
    """Run the pump forward for a specified duration."""
    print(f"  -> Forward ({duration}s)...")
    direction_pin.value = FORWARD_LEVEL  # Set direction
    time.sleep(0.1)  # Short pause to ensure direction is set
    power_pin.on()       # Turn on pump
    time.sleep(duration) # Let it run
    power_pin.off()      # Turn off pump
    print("     Stopped.")

def run_backward(power_pin, direction_pin, duration):
    """Run the pump backward for a specified duration."""
    print(f"  -> Backward ({duration}s)...")
    direction_pin.value = BACKWARD_LEVEL  # Set direction
    time.sleep(0.1)  # Short pause
    power_pin.on()        # Turn on pump
    time.sleep(duration)  # Let it run
    power_pin.off()       # Turn off pump
    print("     Stopped.")

def stop_all_pumps():
    """Stop all successfully initialized pumps immediately."""
    print("\nNOT-STOP: Stopping all initialized pumps...")
    global pump_gpio_devices
    stopped_count = 0
    for pump_id, devices in pump_gpio_devices.items():
        power_pin, _ = devices  # Direction pin is irrelevant here
        if power_pin:
            try:
                power_pin.off()
                stopped_count += 1
            except Exception as e:
                print(f"  ! Error stopping Pump {pump_id}: {e}")
    print(f"{stopped_count} pump(s) stopped.")

def cleanup_gpio():
    """Release all used GPIO resources."""
    print("\nCleaning up GPIO pins...")
    global pump_gpio_devices
    closed_count = 0
    for pump_id, devices in pump_gpio_devices.items():
        power_pin, direction_pin = devices
        try:
            if power_pin:
                power_pin.close()
            if direction_pin:
                direction_pin.close()
            closed_count += 1
        except Exception as e:
            print(f"  ! Error closing pins for Pump {pump_id}: {e}")
    print(f"{closed_count} pump GPIO pairs released.")
    pump_gpio_devices.clear()  # Clear the dictionary

@app.route('/')
def index():
    """Render main page"""
    config = load_config(CONFIG_FILE)
    if config:
        return render_template('index.html', pumps=config)
    return "Error loading configuration", 500

@app.route('/test-pump', methods=['POST'])
def test_pump():
    """Test a single pump"""
    data = request.json
    pump_id = data.get('pump_id')
    direction = data.get('direction')
    config = load_config(CONFIG_FILE)
    
    if not config:
        return jsonify({'success': False, 'message': 'Failed to load configuration'})
    
    # Find pump configuration
    pump_config = next((p for p in config if p['id'] == pump_id), None)
    if not pump_config:
        return jsonify({'success': False, 'message': 'Pump not found'})
    
    try:
        # Setup GPIO and store in global dictionary
        power_pin, direction_pin = setup_pump_gpio(pump_config)
        if not power_pin or not direction_pin:
            return jsonify({'success': False, 'message': f'Failed to setup GPIO for pump {pump_id} (Power: GPIO{pump_config["gpio_pin"]}, Direction: GPIO{pump_config["direction_pin"]})'})
        
        # Store the pins in the global dictionary for cleanup
        pump_gpio_devices[pump_id] = (power_pin, direction_pin)
        
        # Run pump
        if direction == 'forward':
            run_forward(power_pin, direction_pin, TEST_DURATION_SECONDS)
        else:
            run_backward(power_pin, direction_pin, TEST_DURATION_SECONDS)
        
        # Cleanup
        cleanup_gpio()
        
        return jsonify({
            'success': True,
            'message': f'Pump {pump_id} successfully tested'
        })
    except Exception as e:
        return jsonify({
            'success': False,
            'message': f'Error testing pump {pump_id}: {str(e)}'
        })

@app.route('/swap-pins', methods=['POST'])
def swap_pins():
    """Swap the power and direction pins for a pump"""
    try:
        data = request.json
        if not data or 'pump_id' not in data:
            return jsonify({'success': False, 'message': 'Missing pump_id in request'})
        
        pump_id = data['pump_id']
        
        # Load and validate configuration
        with open(CONFIG_FILE, 'r') as f:
            config = json.load(f)
            
        if 'pumps' not in config:
            return jsonify({'success': False, 'message': 'Invalid configuration file structure'})
            
        # Find pump configuration
        pump = next((p for p in config['pumps'] if p['id'] == pump_id), None)
        if not pump:
            return jsonify({'success': False, 'message': f'Pump {pump_id} not found'})
            
        # Swap the pins in the configuration
        temp = pump['gpio_pin']
        pump['gpio_pin'] = pump['direction_pin']
        pump['direction_pin'] = temp
        
        # Save the updated configuration
        with open(CONFIG_FILE, 'w') as f:
            json.dump(config, f, indent=2)
        
        return jsonify({
            'success': True,
            'message': f'Pins swapped for pump {pump_id}',
            'gpio_pin': pump['gpio_pin'],
            'direction_pin': pump['direction_pin']
        })
        
    except json.JSONDecodeError as e:
        return jsonify({
            'success': False,
            'message': f'Invalid JSON in request or configuration file: {str(e)}'
        })
    except Exception as e:
        return jsonify({
            'success': False,
            'message': f'Error swapping pins for pump {pump_id}: {str(e)}'
        })

@app.route('/stop-all', methods=['POST'])
def stop_all():
    """Stop all pumps and cleanup GPIO"""
    stop_all_pumps()
    cleanup_gpio()
    return jsonify({'success': True, 'message': 'All pumps stopped and GPIO cleaned up'})

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=8000)
