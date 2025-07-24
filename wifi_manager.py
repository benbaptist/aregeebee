import network
import time

try:
    from sys import print_exception
except ImportError:
    import traceback
    def print_exception(exc):
        traceback.print_exc()


class WiFiManager:
    def __init__(self, config):
        self.config = config
        self.wlan = None
    
    def connect_wifi(self):
        """Connect to WiFi or start access point"""
        wifi_config = self.config['wifi']
        wifi_mode = wifi_config.get('mode', 'sta')
        
        if wifi_mode == 'ap':
            return self.start_access_point()
        else:
            return self.connect_wifi_station()
    
    def start_access_point(self):
        """Start WiFi access point mode"""
        try:
            self.wlan = network.WLAN(network.AP_IF)
            self.wlan.active(True)
            
            ap_config = self.config['wifi']['ap']
            
            # Configure the access point with only supported parameters
            self.wlan.config(
                essid=ap_config['ssid'],
                password=ap_config['password']
            )
            
            # Wait for AP to become active
            timeout = 10
            while not self.wlan.active() and timeout > 0:
                time.sleep(0.1)
                timeout -= 1
            
            if not self.wlan.active():
                print("✗ Access Point failed to activate")
                return False
            
            print(f"✓ Access Point started: {ap_config['ssid']}")
            print(f"  IP: {self.wlan.ifconfig()[0]}")
            return True
            
        except Exception as e:
            print("✗ Failed to start access point:")
            print(f"  Error: {e}")
            print_exception(e)
            return False
    
    def connect_wifi_station(self):
        """Connect to WiFi in station mode"""
        self.wlan = network.WLAN(network.STA_IF)
        self.wlan.active(True)
        
        wifi_config = self.config['wifi']
        ssid = wifi_config['ssid']
        password = wifi_config['password']
        timeout = wifi_config.get('connection_timeout', 20)
        
        if ssid == "YourWiFiNetwork":
            print("✗ Please configure WiFi credentials in config.json")
            return False
        
        print(f"Connecting to WiFi: {ssid}")
        self.wlan.connect(ssid, password)
        
        while timeout > 0 and not self.wlan.isconnected():
            time.sleep(1)
            timeout -= 1
        
        if self.wlan.isconnected():
            print(f"✓ WiFi connected: {self.wlan.ifconfig()[0]}")
            return True
        else:
            print("✗ WiFi connection failed")
            return False
    
    def check_wifi_connection(self):
        """Check and maintain WiFi connection"""
        wifi_mode = self.config['wifi'].get('mode', 'sta')
        
        if wifi_mode == 'ap':
            return self.wlan and self.wlan.active()
        else:
            return self.wlan and self.wlan.isconnected()
    
    def get_wlan(self):
        """Get the WLAN interface"""
        return self.wlan
