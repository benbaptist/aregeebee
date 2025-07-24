import time
from config_manager import ConfigManager
from wifi_manager import WiFiManager
from udp_server import UDPServer
from mqtt_client import MQTTClientManager
from led_controller import LEDStripController

try:
    from sys import print_exception
except ImportError:
    import traceback
    def print_exception(exc):
        traceback.print_exc()


class LEDController:
    def __init__(self):
        self.config_manager = None
        self.wifi_manager = None
        self.udp_server = None
        self.mqtt_client = None
        self.led_controller = None
        self.config = None
        
    def led_tester_mode(self):
        """LED tester mode - incrementally test LEDs with color cycling"""
        print("Starting LED Tester Mode")
        led_count = 1
        safety_limit = 1000
        
        while led_count <= safety_limit:
            print(f"Testing {led_count} LED(s)")
            
            # Re-initialize strip for current LED count
            self.led_controller.setup(led_count)
            
            # Test colors: Red, Green, Blue, (White if RGBW)
            test_colors = [(255, 0, 0), (0, 255, 0), (0, 0, 255)]
            if self.led_controller.bytes_per_led == 4:
                test_colors.append((0, 0, 0, 255))  # White for RGBW
            
            for color in test_colors:
                self.led_controller.fill_color(color)
                time.sleep(1)
            
            # Clear LEDs
            self.led_controller.clear()
            time.sleep(0.5)
            
            led_count += 1
        
        # Reset after safety limit
        print(f"Safety limit of {safety_limit} LEDs reached. Restarting...")
        self.led_tester_mode()
    
    def normal_operation_mode(self):
        """Normal operation mode - WiFi + UDP/MQTT servers"""
        print("Starting Normal Operation Mode")
        
        # Perform startup test
        if self.config['led'].get('startup_test', True):
            self.led_controller.startup_test()
        
        # Connect to WiFi or start Access Point
        if not self.wifi_manager.connect_wifi():
            wifi_mode = self.config['wifi'].get('mode', 'sta')
            if wifi_mode == 'sta':
                print("Failed to connect to WiFi. Retrying in 5 seconds...")
                time.sleep(5)
                return self.normal_operation_mode()
            else:
                print("Failed to start Access Point. Exiting...")
                return
        
        # Setup servers
        wlan = self.wifi_manager.get_wlan()
        expected_packet_size = self.led_controller.get_expected_packet_size()
        
        udp_ok = self.udp_server.setup(expected_packet_size)
        
        # Link MQTT client to LED controller BEFORE MQTT setup
        # This ensures effects are available during discovery publishing
        self.mqtt_client.set_led_controller(self.led_controller)
        
        mqtt_ok = self.mqtt_client.setup()
        
        if not udp_ok and not mqtt_ok:
            print("Failed to setup any server protocols. Retrying in 5 seconds...")
            time.sleep(5)
            return self.normal_operation_mode()
        
        # Provide status of protocols
        if udp_ok and mqtt_ok:
            print("✓ LED Controller ready - UDP and MQTT protocols active")
        elif udp_ok:
            print("✓ LED Controller ready - UDP protocol active (MQTT failed)")
        elif mqtt_ok:
            print("✓ LED Controller ready - MQTT protocol active (UDP failed)")
        
        # Main operation loop
        wifi_check_counter = 0
        last_status_publish = 0
        status_interval = self.config['system'].get('status_interval', 30)
        
        while True:
            try:
                # Check WiFi connection periodically
                wifi_check_counter += 1
                if wifi_check_counter >= 1000:  # Check every 10 seconds instead of 1 second
                    wifi_check_counter = 0
                    if not self.wifi_manager.check_wifi_connection():
                        self.cleanup()
                        return self.normal_operation_mode()
                
                # Publish status periodically (time-based instead of counter-based)
                current_time = time.time()
                if current_time - last_status_publish >= status_interval:
                    last_status_publish = current_time
                    self.mqtt_client.publish_status()
                
                # Handle UDP packets
                data, addr = self.udp_server.receive_data()
                if data:
                    self.led_controller.process_led_data(data)
                
                # Handle MQTT messages
                self.mqtt_client.check_messages()
                
                time.sleep(0.01)  # Much smaller delay for better responsiveness
                    
            except KeyboardInterrupt:
                print("Operation interrupted")
                break
            except Exception as e:
                print("Unexpected error in main loop:")
                print_exception(e)
                time.sleep(1)
        
        self.cleanup()
    
    def cleanup(self):
        """Cleanup resources"""
        print("Cleaning up...")
        
        if self.mqtt_client:
            self.mqtt_client.cleanup()
        
        if self.udp_server:
            self.udp_server.close()
        
        if self.led_controller:
            self.led_controller.cleanup()
    
    def run(self):
        """Main entry point for the LED controller"""
        print("=== WS2812B LED Strip Controller v2.0 ===")
        
        # Initialize configuration
        self.config_manager = ConfigManager()
        if not self.config_manager.load_config():
            print("Configuration setup required. Please edit config.json and restart.")
            return
        
        self.config = self.config_manager.get_config()
        
        # Initialize components
        self.wifi_manager = WiFiManager(self.config)
        self.udp_server = UDPServer(self.config, None)  # WLAN will be set after connection
        self.mqtt_client = MQTTClientManager(self.config, None)  # WLAN will be set after connection
        self.led_controller = LEDStripController(self.config)
        
        # Check for LED tester mode
        if self.config['system'].get('led_tester_mode', False):
            if not self.led_controller.setup(1):  # Start with 1 LED for tester mode
                print("Failed to setup LED strip. Exiting.")
                return
            self.led_tester_mode()
        else:
            # Normal operation mode
            if not self.led_controller.setup():
                print("Failed to setup LED strip. Exiting.")
                return
            
            # Update server components with WLAN reference after WiFi setup
            self.udp_server.wlan = self.wifi_manager.get_wlan()
            self.mqtt_client.wlan = self.wifi_manager.get_wlan()
            
            self.normal_operation_mode()


# Main execution
if __name__ == "__main__":
    controller = LEDController()
    controller.run()
