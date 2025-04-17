import pygame
import json
import os
import sys
import time
from gpiozero import DigitalOutputDevice, Device
from gpiozero.pins.lgpio import LGPIOFactory

# Set lgpio as the default pin factory
Device.pin_factory = LGPIOFactory()

# Initialize Pygame with better error handling
pygame.init()

# Constants
SCREEN_WIDTH = 480   # Vertical orientation
SCREEN_HEIGHT = 800
FLOW_RATE = 150  # ml per minute
TARGET_VOLUME = 300  # ml total per cocktail
OZ_TO_ML = 29.5735  # 1 fluid ounce = 29.5735 ml

# Colors
BLACK = (0, 0, 0)
WHITE = (255, 255, 255)
BLUE = (0, 123, 255)
GREEN = (40, 167, 69)

def animate_text_zoom(screen, base_text, position, start_size, target_size, duration=300, background=None, current_img=None, image_offset=0):
    """Animate overlay text zooming from a small size to target size."""
    clock = pygame.time.Clock()
    start_time = pygame.time.get_ticks()
    while True:
        elapsed = pygame.time.get_ticks() - start_time
        progress = min(elapsed / duration, 1.0)
        current_size = int(start_size + (target_size - start_size) * progress)
        font = pygame.font.SysFont(None, current_size)
        text_surface = font.render(base_text, True, WHITE)
        text_rect = text_surface.get_rect(center=position)
        if background:
            screen.blit(background, (0, 0))
        if current_img:
            screen.blit(current_img, (image_offset, 0))
        screen.blit(text_surface, text_rect)
        pygame.display.flip()
        if progress >= 1.0:
            break
        clock.tick(60)

def show_mixing_animation(screen, duration_sec, background=None):
    """Show mixing animation with rotating loading image."""
    clock = pygame.time.Clock()
    start_time = pygame.time.get_ticks()
    angle = 0
    
    # Calculate sizes for vertical layout
    loading_size = min(SCREEN_WIDTH - 40, int(SCREEN_HEIGHT * 0.4))  # 40px margin, 40% of height
    
    try:
        # Load and rotate pouring image for vertical layout
        pouring_img = pygame.image.load(os.path.join("drink_logos", "pouring.png"))
        pouring_img = pygame.transform.rotate(pouring_img, -90)
        pouring_img = pygame.transform.scale(pouring_img, (SCREEN_WIDTH, SCREEN_HEIGHT))
        
        # Load and prepare loading spinner
        loading_img = pygame.image.load(os.path.join("drink_logos", "loading.png"))
        loading_img = pygame.transform.scale(loading_img, (loading_size, loading_size))
    except Exception as e:
        print(f"Error loading animation images: {e}")
        return

    # Create progress text
    font = pygame.font.SysFont(None, 48)
    
    while True:
        elapsed = pygame.time.get_ticks() - start_time
        if elapsed >= duration_sec * 1000:
            break
        
        # Calculate progress
        progress = min(elapsed / (duration_sec * 1000), 1.0)
        progress_text = f"Mixing... {int(progress * 100)}%"
        
        # Clear screen
        if background:
            screen.blit(background, (0, 0))
        else:
            screen.fill(BLACK)
        
        # Draw pouring animation
        screen.blit(pouring_img, (0, 0))
        
        # Draw rotating loading spinner
        angle = (angle + 5) % 360
        rotated_loading = pygame.transform.rotate(loading_img, angle)
        rotated_rect = rotated_loading.get_rect(center=(SCREEN_WIDTH // 2, SCREEN_HEIGHT // 2))
        screen.blit(rotated_loading, rotated_rect)
        
        # Draw progress text
        text = font.render(progress_text, True, WHITE)
        text_rect = text.get_rect(center=(SCREEN_WIDTH // 2, SCREEN_HEIGHT - 100))
        screen.blit(text, text_rect)
        
        pygame.display.flip()
        clock.tick(60)

class CocktailMixer:
    def __init__(self):
        self.load_configurations()
        self.load_images()
        self.current_cocktail = 0
        self.mixing = False
        self.start_x = 0
        self.dragging = False
        self.drag_offset = 0
        self.pumps = {}
        self.setup_pumps()
        
    def load_configurations(self):
        # Load cocktails
        with open('cocktails.json', 'r') as f:
            self.cocktails = json.load(f)['cocktails']
            
        # Load pump configuration
        with open('pump_config.json', 'r') as f:
            self.pump_config = json.load(f)
            
    def load_images(self):
        self.images = []
        self.background = None
        
        # Calculate image dimensions for vertical layout
        image_height = int(SCREEN_HEIGHT * 0.6)  # Use 60% of screen height for images
        image_width = SCREEN_WIDTH - 40  # Leave 20px margin on each side
        
        # Load background
        try:
            self.background = pygame.image.load(os.path.join("drink_logos", "tipsy.png"))
            # Rotate and scale background for vertical orientation
            self.background = pygame.transform.rotate(self.background, -90)
            self.background = pygame.transform.scale(self.background, (SCREEN_WIDTH, SCREEN_HEIGHT))
        except Exception as e:
            print(f"Error loading background: {e}")
        
        # Load drink images
        for cocktail in self.cocktails:
            name = cocktail['normal_name'].lower().replace(' ', '_')
            try:
                image_path = os.path.join('drink_logos', f"{name}.png")
                if not os.path.exists(image_path):
                    alternatives = [
                        name.replace('_', ' ').title().replace(' ', '_'),
                        name.capitalize()
                    ]
                    for alt_name in alternatives:
                        alt_path = os.path.join('drink_logos', f"{alt_name}.png")
                        if os.path.exists(alt_path):
                            image_path = alt_path
                            break
                
                # Load and process image
                image = pygame.image.load(image_path)
                # Rotate image for vertical orientation
                image = pygame.transform.rotate(image, -90)
                # Scale while maintaining aspect ratio
                img_rect = image.get_rect()
                scale = min(image_width / img_rect.width, image_height / img_rect.height)
                new_size = (int(img_rect.width * scale), int(img_rect.height * scale))
                image = pygame.transform.scale(image, new_size)
                
                # Create a surface with the target size
                final_surface = pygame.Surface((image_width, image_height))
                final_surface.fill(BLACK)
                # Center the image on the surface
                x = (image_width - new_size[0]) // 2
                y = (image_height - new_size[1]) // 2
                final_surface.blit(image, (x, y))
                
                self.images.append((final_surface, cocktail['normal_name']))
            except Exception as e:
                print(f"Could not load image for {name}: {e}")
                # Create a placeholder
                placeholder = pygame.Surface((image_width, image_height))
                placeholder.fill(BLUE)
                self.images.append((placeholder, cocktail['normal_name']))

    def setup_pumps(self):
        for pump_name, ingredient in self.pump_config.items():
            pump_num = int(pump_name.split()[1])
            gpio_pin = self.get_gpio_pin(pump_num)
            if gpio_pin:
                self.pumps[ingredient.lower()] = DigitalOutputDevice(gpio_pin)

    def get_gpio_pin(self, pump_num):
        pump_to_gpio = {
            1: 27, 2: 17, 3: 18, 4: 23, 5: 5, 6: 6, 7: 13,
            8: 19, 9: 20, 10: 21
        }
        return pump_to_gpio.get(pump_num)

    def animate_swipe(self, direction, duration=300):
        """Animate smooth swipe transition."""
        start_time = pygame.time.get_ticks()
        start_offset = self.drag_offset
        target_offset = SCREEN_WIDTH if direction > 0 else -SCREEN_WIDTH
        
        while True:
            elapsed = pygame.time.get_ticks() - start_time
            progress = min(elapsed / duration, 1.0)
            current_offset = start_offset + (target_offset - start_offset) * progress
            
            self.draw(current_offset)
            
            if progress >= 1.0:
                break
            
            pygame.time.Clock().tick(60)

    def mix_cocktail(self):
        if self.mixing:
            return
            
        self.mixing = True
        cocktail = self.cocktails[self.current_cocktail]
        
        # Show mixing animation
        show_mixing_animation(screen, 10, self.background)
        
        # Calculate and run pumps
        for ingredient, amount in cocktail['ingredients'].items():
            if 'dash' not in amount.lower():
                oz = float(amount.split()[0])
                ml = oz * OZ_TO_ML
                
                ingredient_lower = ingredient.lower()
                if ingredient_lower in self.pumps:
                    pump = self.pumps[ingredient_lower]
                    duration = (ml / FLOW_RATE) * 60
                    
                    pump.on()
                    time.sleep(duration)
                    pump.off()
        
        self.mixing = False

    def draw(self, offset=0):
        if self.background:
            screen.blit(self.background, (0, 0))
        else:
            screen.fill(BLACK)
        
        # Draw current cocktail
        current_img, current_name = self.images[self.current_cocktail]
        # Calculate image position to center in the top portion
        img_y = 50  # Leave space at top
        screen.blit(current_img, (offset, img_y))
        
        # Draw adjacent cocktails if dragging
        if offset < 0:
            next_idx = (self.current_cocktail + 1) % len(self.images)
            next_img, _ = self.images[next_idx]
            screen.blit(next_img, (SCREEN_WIDTH + offset, img_y))
        elif offset > 0:
            prev_idx = (self.current_cocktail - 1) % len(self.images)
            prev_img, _ = self.images[prev_idx]
            screen.blit(prev_img, (-SCREEN_WIDTH + offset, img_y))
        
        # Draw cocktail name
        font = pygame.font.SysFont(None, 48)
        text = font.render(current_name, True, WHITE)
        text_rect = text.get_rect(center=(SCREEN_WIDTH // 2, SCREEN_HEIGHT - 150))
        screen.blit(text, text_rect)
        
        # Draw emergency stop button
        stop_button_rect = pygame.Rect(20, SCREEN_HEIGHT - 100, SCREEN_WIDTH - 40, 80)
        # Draw button shadow
        shadow_rect = stop_button_rect.copy()
        shadow_rect.y += 4
        pygame.draw.rect(screen, (100, 0, 0), shadow_rect, border_radius=10)
        # Draw main button
        pygame.draw.rect(screen, (200, 0, 0), stop_button_rect, border_radius=10)
        pygame.draw.rect(screen, (255, 0, 0), stop_button_rect.inflate(-4, -4), border_radius=10)
        
        # Draw stop icon and text
        font = pygame.font.SysFont(None, 36)
        stop_text = font.render("EMERGENCY STOP", True, WHITE)
        stop_text_rect = stop_text.get_rect(center=stop_button_rect.center)
        screen.blit(stop_text, stop_text_rect)
        
        pygame.display.flip()
        
        return stop_button_rect  # Return the stop button rect for click detection

    def emergency_stop(self):
        """Stop all pumps immediately"""
        print("EMERGENCY STOP - Stopping all pumps")
        for pump in self.pumps.values():
            pump.off()
        self.mixing = False
        
        # Show emergency stop message
        font = pygame.font.SysFont(None, 72)
        text = font.render("EMERGENCY STOP", True, WHITE)
        text_rect = text.get_rect(center=(SCREEN_WIDTH // 2, SCREEN_HEIGHT // 2))
        
        overlay = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT))
        overlay.fill((200, 0, 0))
        overlay.set_alpha(200)
        
        screen.blit(overlay, (0, 0))
        screen.blit(text, text_rect)
        pygame.display.flip()
        
        # Wait a moment to show the message
        pygame.time.wait(2000)

    def handle_event(self, event):
        if event.type == pygame.MOUSEBUTTONDOWN:
            # Check for emergency stop button click
            stop_button_rect = self.draw()  # Get the current stop button rect
            if stop_button_rect.collidepoint(event.pos):
                self.emergency_stop()
                return
                
            self.dragging = True
            self.start_x = event.pos[0]
            
        elif event.type == pygame.MOUSEMOTION and self.dragging:
            self.drag_offset = event.pos[0] - self.start_x
            
        elif event.type == pygame.MOUSEBUTTONUP and self.dragging:
            # Handle click vs swipe
            if abs(self.drag_offset) < 50:  # Click
                if not self.mixing:
                    self.mix_cocktail()
            else:  # Swipe
                if abs(self.drag_offset) > SCREEN_WIDTH / 3:
                    direction = 1 if self.drag_offset > 0 else -1
                    self.animate_swipe(direction)
                    self.current_cocktail = (self.current_cocktail - direction) % len(self.images)
                else:
                    self.animate_swipe(0)  # Snap back
            
            self.dragging = False
            self.drag_offset = 0

def init_display():
    """Initialize the display for Raspberry Pi"""
    print("\nInitializing display...")
    print(f"Current environment:")
    print(f"DISPLAY: {os.environ.get('DISPLAY', 'Not set')}")
    print(f"SDL_VIDEODRIVER: {os.environ.get('SDL_VIDEODRIVER', 'Not set')}")
    
    try:
        # Initialize pygame display
        pygame.display.init()
        print("Pygame display initialized")
        
        # Try different display modes
        try_modes = [
            (pygame.FULLSCREEN | pygame.SCALED, "Fullscreen scaled"),
            (pygame.FULLSCREEN, "Fullscreen"),
            (pygame.SCALED, "Scaled window"),
            (0, "Default window")
        ]
        
        last_error = None
        for flags, mode_name in try_modes:
            try:
                print(f"\nTrying {mode_name} mode...")
                screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT), flags)
                print(f"Success! Using {mode_name} mode")
                print(f"Actual display size: {screen.get_size()}")
                pygame.display.set_caption("Mix-a-Lot")
                return screen
            except pygame.error as e:
                last_error = e
                print(f"Failed to set {mode_name} mode: {e}")
                continue
        
        # If we get here, no mode worked
        raise last_error or pygame.error("Could not initialize any display mode")
        
    except pygame.error as e:
        print(f"\nFatal error initializing display: {e}")
        print("\nDebug information:")
        print(f"Python version: {sys.version}")
        print(f"Pygame version: {pygame.version.ver}")
        print(f"Working directory: {os.getcwd()}")
        print("\nPlease ensure:")
        print("1. X server is running")
        print("2. DISPLAY environment variable is set correctly")
        print("3. You have permission to access the X server")
        sys.exit(1)

def main():
    global screen
    screen = init_display()
    
    mixer = CocktailMixer()
    clock = pygame.time.Clock()
    running = True
    
    while running:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
            elif event.type == pygame.KEYDOWN:
                if event.key == pygame.K_ESCAPE:
                    running = False
            else:
                mixer.handle_event(event)
        
        mixer.draw(mixer.drag_offset if mixer.dragging else 0)
        clock.tick(60)
    
    pygame.quit()

if __name__ == '__main__':
    main()
