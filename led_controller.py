import time
from neopixel import Neopixel

try:
    from sys import print_exception
except ImportError:
    import traceback
    def print_exception(exc):
        traceback.print_exc()


class LEDStripController:
    def __init__(self, config):
        self.config = config
        self.strip = None
        self.bytes_per_led = 3
        self.expected_packet_size = 0
        
        # Home Assistant state tracking
        self._current_state = "OFF"
        self._current_brightness = 255
        self._current_color = None
        self._current_effect = "none"
        
        # Available effects - can be extended
        self._available_effects = [
            "none",
            "rainbow", 
            "chase",
            "fade",
            "strobe",
            "color_wipe",
            "theater_chase",
            "rainbow_cycle"
        ]
    
    def setup(self, led_count=None):
        """Setup LED strip"""
        led_config = self.config['led']
        
        if led_count is None:
            led_count = led_config['count']
        
        if led_count <= 0:
            print("✗ Invalid LED count")
            return False
        
        led_mode = led_config.get('mode', 'RGB').upper()
        
        # Determine bytes per LED based on mode
        if 'W' in led_mode:
            self.bytes_per_led = 4  # RGBW
        else:
            self.bytes_per_led = 3  # RGB
        
        self.expected_packet_size = led_count * self.bytes_per_led
        
        try:
            self.strip = Neopixel(
                num_leds=led_count,
                state_machine=led_config.get('state_machine', 0),
                pin=led_config.get('pin', 28),
                mode=led_mode,
                delay=led_config.get('delay', 0.0003)
            )
            
            # Set initial brightness
            initial_brightness = led_config.get('brightness', 255)
            self.strip.brightness(initial_brightness)
            self._current_brightness = initial_brightness
            
            print(f"✓ LED strip initialized: {led_count} LEDs, {led_mode} mode")
            return True
            
        except Exception as e:
            print("✗ Failed to initialize LED strip:")
            print_exception(e)
            return False
    
    def startup_test(self):
        """Perform startup LED test"""
        if not self.strip:
            return
            
        print("Running LED startup test...")
        
        # Test red
        self.strip.fill((255, 0, 0))
        self.strip.show()
        time.sleep(0.5)
        
        # Test green
        self.strip.fill((0, 255, 0))
        self.strip.show()
        time.sleep(0.5)
        
        # Test blue
        self.strip.fill((0, 0, 255))
        self.strip.show()
        time.sleep(0.5)
        
        # Clear
        self.strip.clear()
        self.strip.show()
        
        print("✓ LED test complete")
    
    def process_led_data(self, data):
        """Process incoming LED data and update the strip"""
        if not self.strip:
            return False
            
        if len(data) != self.expected_packet_size:
            if self.config['system'].get('debug', False):
                print(f"Invalid packet size: {len(data)} bytes (expected {self.expected_packet_size})")
            return False
        
        try:
            led_count = self.config['led'].get('count', 50)
            
            for i in range(led_count):
                offset = i * self.bytes_per_led
                
                if self.bytes_per_led == 4:  # RGBW
                    r = data[offset]
                    g = data[offset + 1]
                    b = data[offset + 2]
                    w = data[offset + 3]
                    self.strip.set_pixel(i, (r, g, b, w))
                else:  # RGB
                    r = data[offset]
                    g = data[offset + 1]
                    b = data[offset + 2]
                    self.strip.set_pixel(i, (r, g, b))
            
            self.strip.show()
            return True
            
        except Exception as e:
            print("✗ Error processing LED data:")
            print_exception(e)
            return False
    
    def fill_color(self, color):
        """Fill strip with single color"""
        if not self.strip:
            return
            
        if self.bytes_per_led == 4 and len(color) == 3:
            color = color + [0]  # Add white component
        
        self.strip.fill(tuple(color))
        self.strip.show()
        self._current_color = tuple(color)
        self._current_state = "ON"
    
    def clear(self):
        """Clear the strip"""
        if not self.strip:
            return
            
        self.strip.clear()
        self.strip.show()
        self._current_state = "OFF"
    
    def set_brightness(self, brightness):
        """Set strip brightness"""
        if not self.strip:
            return
            
        self.strip.brightness(brightness)
        self.strip.show()
        self._current_brightness = brightness
    
    def process_ha_command(self, command):
        """Process Home Assistant JSON commands"""
        if not self.strip:
            return
            
        if self.config['system'].get('debug', False):
            print(f"Processing HA command: {command}")
        
        # Handle state changes
        if "state" in command:
            if command["state"] == "ON":
                self._current_state = "ON"
                
                if "brightness" in command:
                    self._current_brightness = command["brightness"]
                    self.strip.brightness(command["brightness"])
                
                if "color" in command:
                    color = command["color"]
                    if self.bytes_per_led == 4:  # RGBW
                        if "w" in color:
                            fill_color = (color.get("r", 0), color.get("g", 0), color.get("b", 0), color.get("w", 0))
                        else:
                            fill_color = (color.get("r", 0), color.get("g", 0), color.get("b", 0), 0)
                    else:  # RGB
                        fill_color = (color.get("r", 0), color.get("g", 0), color.get("b", 0))
                    
                    self._current_color = fill_color
                    # Only fill if no effect is specified or effect is "none"
                    effect = command.get("effect", self._current_effect)
                    if effect == "none":
                        self.strip.fill(fill_color)
                
                if "effect" in command:
                    self._handle_effect(command["effect"])
                
                if "color" not in command and "effect" not in command:
                    # Just turn on with previous color or white
                    if self._current_color:
                        self.strip.fill(self._current_color)
                    else:
                        if self.bytes_per_led == 4:
                            default_color = (255, 255, 255, 0)
                        else:
                            default_color = (255, 255, 255)
                        self._current_color = default_color
                        self.strip.fill(default_color)
                
                # Only show if no effect is running (effects handle their own showing)
                if command.get("effect", self._current_effect) == "none":
                    self.strip.show()
                
            elif command["state"] == "OFF":
                self._current_state = "OFF"
                self._current_effect = "none"  # Reset effect when turning off
                self.strip.clear()
                self.strip.show()
        
        # Handle brightness only changes
        elif "brightness" in command:
            self._current_brightness = command["brightness"]
            self.strip.brightness(command["brightness"])
            # Re-apply current effect or color
            if self._current_effect != "none":
                self._handle_effect(self._current_effect)
            elif self._current_color:
                self.strip.fill(self._current_color)
                self.strip.show()
        
        # Handle color only changes
        elif "color" in command:
            color = command["color"]
            if self.bytes_per_led == 4:  # RGBW
                if "w" in color:
                    fill_color = (color.get("r", 0), color.get("g", 0), color.get("b", 0), color.get("w", 0))
                else:
                    fill_color = (color.get("r", 0), color.get("g", 0), color.get("b", 0), 0)
            else:  # RGB
                fill_color = (color.get("r", 0), color.get("g", 0), color.get("b", 0))
            
            # Only update if color actually changed to avoid unnecessary operations
            if fill_color != self._current_color:
                self._current_color = fill_color
                self.strip.fill(fill_color)
                self.strip.show()
                if self._current_state == "OFF":
                    self._current_state = "ON"
        
        # Handle effect changes
        elif "effect" in command:
            self._handle_effect(command["effect"])
    
    def get_available_effects(self):
        """Get list of available effects"""
        return self._available_effects.copy()
    
    def add_effect(self, effect_name):
        """Add a new effect to the available list"""
        if effect_name not in self._available_effects:
            self._available_effects.append(effect_name)
            return True
        return False
    
    def remove_effect(self, effect_name):
        """Remove an effect from the available list (cannot remove 'none')"""
        if effect_name != "none" and effect_name in self._available_effects:
            self._available_effects.remove(effect_name)
            # If current effect was removed, switch to none
            if self._current_effect == effect_name:
                self._current_effect = "none"
            return True
        return False
    
    def _handle_effect(self, effect_name):
        """Handle LED effects"""
        if not self.strip:
            return
            
        if self.config['system'].get('debug', False):
            print(f"Setting effect: {effect_name}")
            
        # Validate effect name
        if effect_name not in self._available_effects:
            print(f"Unknown effect: {effect_name}, available: {self._available_effects}")
            return
            
        self._current_effect = effect_name
        if effect_name == "none":
            # No effect, just solid color
            if self._current_color is not None:
                self.strip.fill(self._current_color)
            else:
                # Default to white
                if self.bytes_per_led == 4:
                    self.strip.fill((255, 255, 255, 0))
                else:
                    self.strip.fill((255, 255, 255))
            self.strip.show()
        elif effect_name == "rainbow":
            self._rainbow_effect()
        elif effect_name == "chase":
            self._chase_effect()
        elif effect_name == "fade":
            self._fade_effect()
        elif effect_name == "strobe":
            self._strobe_effect()
        elif effect_name == "color_wipe":
            self._color_wipe_effect()
        elif effect_name == "theater_chase":
            self._theater_chase_effect()
        elif effect_name == "rainbow_cycle":
            self._rainbow_cycle_effect()
    
    def _rainbow_effect(self):
        """Simple rainbow effect"""
        try:
            led_count = self.config['led'].get('count', 50)
            
            for i in range(led_count):
                hue = (i * 360 // led_count) % 360
                r, g, b = self._hsv_to_rgb(hue, 100, 100)
                if self.bytes_per_led == 4:
                    self.strip.set_pixel(i, (r, g, b, 0))
                else:
                    self.strip.set_pixel(i, (r, g, b))
            self.strip.show()
        except Exception as e:
            print("Rainbow effect error:")
            print_exception(e)
    
    def _chase_effect(self):
        """Simple chase effect"""
        try:
            led_count = self.config['led'].get('count', 50)
            
            self.strip.clear()
            # Light up every 3rd LED
            for i in range(0, led_count, 3):
                if self.bytes_per_led == 4:
                    self.strip.set_pixel(i, (255, 255, 255, 0))
                else:
                    self.strip.set_pixel(i, (255, 255, 255))
            self.strip.show()
        except Exception as e:
            print("Chase effect error:")
            print_exception(e)
    
    def _fade_effect(self):
        """Simple fade effect"""
        try:
            brightness = 128  # Half brightness
            if self.bytes_per_led == 4:
                self.strip.fill((brightness, brightness, brightness, brightness))
            else:
                self.strip.fill((brightness, brightness, brightness))
            self.strip.show()
        except Exception as e:
            print("Fade effect error:")
            print_exception(e)
    
    def _strobe_effect(self):
        """Strobe effect"""
        try:
            led_count = self.config['led'].get('count', 50)
            
            # Flash white
            if self.bytes_per_led == 4:
                self.strip.fill((255, 255, 255, 0))
            else:
                self.strip.fill((255, 255, 255))
            self.strip.show()
            
        except Exception as e:
            print("Strobe effect error:")
            print_exception(e)
    
    def _color_wipe_effect(self):
        """Color wipe effect - fills LEDs one by one"""
        try:
            led_count = self.config['led'].get('count', 50)
            
            # Use current color or default to red
            color = self._current_color if self._current_color else (255, 0, 0)
            if self.bytes_per_led == 4 and len(color) == 3:
                color = color + (0,)
            
            # Light up first 10 LEDs for demo
            self.strip.clear()
            for i in range(min(10, led_count)):
                self.strip.set_pixel(i, color)
            self.strip.show()
            
        except Exception as e:
            print("Color wipe effect error:")
            print_exception(e)
    
    def _theater_chase_effect(self):
        """Theater chase effect"""
        try:
            led_count = self.config['led'].get('count', 50)
            
            # Use current color or default to blue
            color = self._current_color if self._current_color else (0, 0, 255)
            if self.bytes_per_led == 4 and len(color) == 3:
                color = color + (0,)
            
            self.strip.clear()
            # Light up every 3rd LED starting from 0
            for i in range(0, led_count, 3):
                self.strip.set_pixel(i, color)
            self.strip.show()
            
        except Exception as e:
            print("Theater chase effect error:")
            print_exception(e)
    
    def _rainbow_cycle_effect(self):
        """Rainbow cycle effect - smoother rainbow"""
        try:
            led_count = self.config['led'].get('count', 50)
            
            for i in range(led_count):
                # Create a cycling rainbow effect
                hue = (i * 256 // led_count) % 256
                r, g, b = self._wheel(hue)
                if self.bytes_per_led == 4:
                    self.strip.set_pixel(i, (r, g, b, 0))
                else:
                    self.strip.set_pixel(i, (r, g, b))
            self.strip.show()
            
        except Exception as e:
            print("Rainbow cycle effect error:")
            print_exception(e)
    
    def _wheel(self, pos):
        """Generate rainbow colors across 0-255 positions"""
        if pos < 85:
            return (pos * 3, 255 - pos * 3, 0)
        elif pos < 170:
            pos -= 85
            return (255 - pos * 3, 0, pos * 3)
        else:
            pos -= 170
            return (0, pos * 3, 255 - pos * 3)
    
    def _hsv_to_rgb(self, h, s, v):
        """Convert HSV to RGB"""
        h = h / 360.0
        s = s / 100.0
        v = v / 100.0
        
        i = int(h * 6)
        f = h * 6 - i
        p = v * (1 - s)
        q = v * (1 - f * s)
        t = v * (1 - (1 - f) * s)
        
        if i % 6 == 0:
            r, g, b = v, t, p
        elif i % 6 == 1:
            r, g, b = q, v, p
        elif i % 6 == 2:
            r, g, b = p, v, t
        elif i % 6 == 3:
            r, g, b = p, q, v
        elif i % 6 == 4:
            r, g, b = t, p, v
        else:
            r, g, b = v, p, q
        
        return int(r * 255), int(g * 255), int(b * 255)
    
    def get_ha_state(self):
        """Get current state for Home Assistant"""
        led_config = self.config['led']
        
        state_payload = {
            "state": self._current_state,
            "brightness": self._current_brightness,
            "effect": self._current_effect
        }
        
        # Add current color if available
        if self._current_color is not None:
            led_mode = led_config.get('mode', 'RGB')
            if led_mode and 'W' in led_mode.upper() and len(self._current_color) == 4:
                state_payload["color_mode"] = "rgbw"
                state_payload["color"] = {
                    "r": self._current_color[0],
                    "g": self._current_color[1], 
                    "b": self._current_color[2],
                    "w": self._current_color[3]
                }
            elif led_mode and len(self._current_color) >= 3:
                state_payload["color_mode"] = "rgb"
                state_payload["color"] = {
                    "r": self._current_color[0],
                    "g": self._current_color[1],
                    "b": self._current_color[2]
                }
        else:
            state_payload["color_mode"] = "brightness"
        
        # Add device information
        state_payload["led_count"] = led_config.get('count', 50)
        state_payload["led_mode"] = led_config.get('mode', 'RGB')
        
        return state_payload
    
    def get_expected_packet_size(self):
        """Get expected packet size"""
        return self.expected_packet_size
    
    def cleanup(self):
        """Cleanup LED resources"""
        if self.strip:
            try:
                self.strip.clear()
                self.strip.show()
            except:
                pass
