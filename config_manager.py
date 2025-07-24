import json
import os
import network

try:
    from sys import print_exception
except ImportError:
    import traceback
    def print_exception(exc):
        traceback.print_exc()


class ConfigManager:
    def __init__(self):
        self.config = None
    
    def get_mac_address(self):
        """Get the MAC address of the Pico and format it as a string"""
        try:
            wlan = network.WLAN(network.STA_IF)
            wlan.active(True)
            mac_bytes = wlan.config('mac')
            mac_str = ':'.join(['%02x' % b for b in mac_bytes])
            wlan.active(False)
            return mac_str
        except Exception as e:
            print(f"Warning: Could not get MAC address: {e}")
            return "00:00:00:00:00:00"
    
    def generate_unique_client_id(self):
        """Generate a unique client ID based on MAC address"""
        mac = self.get_mac_address()
        mac_suffix = mac.replace(':', '')[-6:]
        return f"pico-led-{mac_suffix}"
        
    def generate_default_config(self):
        """Generate a default configuration file"""
        unique_client_id = self.generate_unique_client_id()
        
        default_config = {
            "description": "AreGeeBee WS2812B LED Strip Controller Configuration",
            "version": "2.0",
            
            "wifi": {
                "mode": "ap",
                "ssid": "YourWiFiNetwork",
                "password": "YourWiFiPassword",
                "connection_timeout": 20,
                "ap": {
                    "ssid": f"AreGeeBee-{unique_client_id[-6:]}",
                    "password": "ledcontroller123"
                }
            },
            
            "led": {
                "count": 4,
                "mode": "RGB",
                "pin": 28,
                "state_machine": 0,
                "delay": 0.0003,
                "brightness": 255,
                "startup_test": True
            },
            
            "server": {
                "udp": {
                    "enabled": False,
                    "ip": "0.0.0.0",
                    "port": 8000,
                    "timeout": 1.0
                },
                "mqtt": {
                    "enabled": False,
                    "broker": "192.168.1.100",
                    "port": 1883,
                    "username": "",
                    "password": "",
                    "client_id": unique_client_id,
                    "keepalive": 60,
                    "ssl": False,
                    "topics": {
                        "led_data": "led/data",
                        "led_command": "led/command",
                        "status": "led/status"
                    },
                    "qos": 0
                }
            },
            
            "system": {
                "led_tester_mode": False,
                "debug": False,
                "status_interval": 30,
                "memory_monitor": False
            }
        }
        
        try:
            with open('config.json', 'w') as f:
                json.dump(default_config, f)
            print("✓ Default configuration generated")
            return default_config
        except Exception as e:
            print(f"✗ Error generating config: {e}")
            return None
    
    def load_config(self):
        """Load configuration from config.json file"""
        if not self._file_exists('config.json'):
            print("Configuration file not found. Generating default config...")
            self.config = self.generate_default_config()
            return self.config is not None
        
        try:
            with open('config.json', 'r') as f:
                self.config = json.load(f)
            
            if not self._validate_config():
                print("Config validation failed. Generating new config...")
                self.config = self.generate_default_config()
                return self.config is not None
            
            print("✓ Configuration loaded")
            return True
            
        except Exception as e:
            print("✗ Error loading config:")
            print_exception(e)
            self.config = self.generate_default_config()
            return False
    
    def _file_exists(self, filename):
        """Check if a file exists"""
        try:
            os.stat(filename)
            return True
        except OSError:
            return False
    
    def _validate_config(self):
        """Validate config structure"""
        required_sections = ['wifi', 'led', 'server', 'system']
        for section in required_sections:
            if section not in self.config:
                return False
        
        # Add AP config if missing
        wifi_config = self.config['wifi']
        wifi_mode = wifi_config.get('mode', 'sta')
        
        if wifi_mode == 'ap' and 'ap' not in wifi_config:
            unique_client_id = self.generate_unique_client_id()
            wifi_config['ap'] = {
                "ssid": f"LED-Controller-{unique_client_id[-6:]}",
                "password": "ledcontroller123"
            }
        
        return True
    
    def get_config(self):
        """Get the loaded configuration"""
        return self.config
