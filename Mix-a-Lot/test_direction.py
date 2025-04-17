from flask import Flask
import json
import time
from gpiozero import DigitalOutputDevice, GPIOZeroError, Device
from gpiozero.pins.lgpio import LGPIOFactory

# Set lgpio as the default pin factory
Device.pin_factory = LGPIOFactory()

# Constants
CONFIG_FILE = 'pumpen.json'
TEST_DURATION = 2.0  # Duration for each test
FORWARD_LEVEL = 0    # Level for forward direction
BACKWARD_LEVEL = 1   # Level for backward direction

def load_config():
    """Load pump configuration from JSON file."""
    with open(CONFIG_FILE, 'r') as f:
        return json.load(f)['pumps']

def test_pump_direction(pump_config):
    """Test a single pump in both directions."""
    try:
        pump_id = pump_config['id']
        power_pin = DigitalOutputDevice(pump_config['gpio_pin'], initial_value=False)
        direction_pin = DigitalOutputDevice(pump_config['direction_pin'], initial_value=False)
        
        print(f"\nTesting Pump {pump_id} ({pump_config['assigned_liquid']})")
        print(f"Power Pin: GPIO{pump_config['gpio_pin']}")
        print(f"Direction Pin: GPIO{pump_config['direction_pin']}")
        
        # Test Forward
        input(f"\nPress Enter to test FORWARD direction (Direction Pin = {FORWARD_LEVEL})...")
        direction_pin.value = FORWARD_LEVEL
        time.sleep(0.1)
        print("Running pump...")
        power_pin.on()
        time.sleep(TEST_DURATION)
        power_pin.off()
        
        response = input("\nDid liquid flow in the EXPECTED direction? (y/n): ").lower()
        if response != 'y':
            print("Direction might be reversed. You can:")
            print("1. Swap the direction pin value (change FORWARD_LEVEL in app.py)")
            print("2. Swap the physical tubes")
            print("3. Swap the direction pin connections")
        
        # Test Backward
        input(f"\nPress Enter to test BACKWARD direction (Direction Pin = {BACKWARD_LEVEL})...")
        direction_pin.value = BACKWARD_LEVEL
        time.sleep(0.1)
        print("Running pump...")
        power_pin.on()
        time.sleep(TEST_DURATION)
        power_pin.off()
        
        response = input("\nDid liquid flow in the EXPECTED direction? (y/n): ").lower()
        if response != 'y':
            print("Direction might be reversed. You can:")
            print("1. Swap the direction pin value (change FORWARD_LEVEL in app.py)")
            print("2. Swap the physical tubes")
            print("3. Swap the direction pin connections")
        
        # Cleanup
        power_pin.close()
        direction_pin.close()
        
    except Exception as e:
        print(f"Error testing pump {pump_id}: {e}")

def main():
    """Main test function."""
    print("=== Pump Direction Testing Utility ===")
    print("\nThis utility will help test each pump's direction.")
    print("For each pump, it will:")
    print("1. Test forward direction")
    print("2. Test backward direction")
    print("\nMake sure you have:")
    print("- A container to catch liquid")
    print("- Paper towels for spills")
    print("- Knowledge of which direction is 'forward' for your setup")
    
    pumps = load_config()
    
    while True:
        print("\nAvailable pumps:")
        for pump in pumps:
            print(f"{pump['id']}: {pump['assigned_liquid']}")
        print("0: Exit")
        
        try:
            choice = int(input("\nEnter pump number to test (0 to exit): "))
            if choice == 0:
                break
            
            pump = next((p for p in pumps if p['id'] == choice), None)
            if pump:
                test_pump_direction(pump)
            else:
                print("Invalid pump number!")
        except ValueError:
            print("Please enter a valid number!")
        except KeyboardInterrupt:
            print("\nTesting interrupted!")
            break

if __name__ == '__main__':
    try:
        main()
    except KeyboardInterrupt:
        print("\nTesting terminated!")
    finally:
        print("\nTest complete!")
