import json
import time

try:
    from sys import print_exception
except ImportError:
    import traceback
    def print_exception(exc):
        traceback.print_exc()


class MQTTClientManager:
    def __init__(self, config, wlan):
        self.config = config
        self.wlan = wlan
        self.mqtt_client = None
        self.led_controller = None  # Will be set by main controller
        self.connected = False
        self.last_connection_attempt = 0
        self.connection_retry_interval = 30  # Retry every 30 seconds
        self.last_state_publish = 0
        self.state_publish_debounce = 0.1  # Only publish state every 100ms max
    
    def setup(self):
        """Setup MQTT client for receiving LED data"""
        if not self.config['server']['mqtt']['enabled']:
            return True
            
        try:
            # Import MQTT client
            try:
                from umqtt.simple import MQTTClient
            except ImportError:
                print("✗ MQTT library not found (umqtt.simple)")
                return False
            
            mqtt_config = self.config['server']['mqtt']
            
            if mqtt_config['broker'] == "192.168.1.100":
                print("✗ Please configure MQTT broker in config.json")
                return False
            
            # Create MQTT client
            self.mqtt_client = MQTTClient(
                client_id=mqtt_config['client_id'],
                server=mqtt_config['broker'],
                port=mqtt_config['port'],
                user=mqtt_config['username'] if mqtt_config['username'] else None,
                password=mqtt_config['password'] if mqtt_config['password'] else None,
                keepalive=mqtt_config['keepalive'],
                ssl=mqtt_config['ssl']
            )
            
            # Set callback for incoming messages
            self.mqtt_client.set_callback(self._mqtt_callback)
            
            # Try to connect to broker
            return self._connect_mqtt()
            
        except Exception as e:
            print("✗ Failed to setup MQTT client:")
            print_exception(e)
            return False
    
    def _connect_mqtt(self):
        """Connect to MQTT broker with error handling"""
        try:
            mqtt_config = self.config['server']['mqtt']
            
            # Connect to broker
            self.mqtt_client.connect()
            self.connected = True
            
            # Subscribe to topics
            topics = mqtt_config['topics']
            self.mqtt_client.subscribe(topics['led_data'])
            self.mqtt_client.subscribe(topics['led_command'])
            
            # Subscribe to Home Assistant discovery topics
            ha_topics = self._get_ha_topics()
            self.mqtt_client.subscribe(ha_topics['command'])
            
            print(f"✓ MQTT connected to {mqtt_config['broker']}:{mqtt_config['port']}")
            
            # Publish Home Assistant discovery message
            self._publish_ha_discovery()
            
            return True
            
        except Exception as e:
            self.connected = False
            print(f"✗ MQTT connection failed: {e}")
            if self.config['system'].get('debug', False):
                print_exception(e)
            return False
    
    def set_led_controller(self, led_controller):
        """Set reference to LED controller for processing commands"""
        self.led_controller = led_controller
    
    def is_connected(self):
        """Check if MQTT client is connected"""
        return self.connected
    
    def _get_ha_topics(self):
        """Get Home Assistant discovery topic structure"""
        device_id = self.config['server']['mqtt']['client_id']
        return {
            'discovery': f"homeassistant/light/{device_id}/config",
            'command': f"homeassistant/light/{device_id}/set",
            'state': f"homeassistant/light/{device_id}/state",
            'availability': f"homeassistant/light/{device_id}/availability"
        }
    
    def _publish_ha_discovery(self):
        """Publish Home Assistant MQTT Discovery message"""
        try:
            device_id = self.config['server']['mqtt']['client_id']
            ha_topics = self._get_ha_topics()
            led_config = self.config['led']
            
            # Determine supported color modes
            led_mode = led_config.get('mode', 'RGB')
            if led_mode and 'W' in led_mode.upper():
                supported_color_modes = ["rgbw"]
            elif led_mode:
                supported_color_modes = ["rgb"]
            else:
                supported_color_modes = ["brightness"]
            
            # Get available effects from LED controller
            effect_list = ["none"]  # Default fallback
            if self.led_controller:
                try:
                    effect_list = self.led_controller.get_available_effects()
                    print(f"✓ Got {len(effect_list)} effects from LED controller: {effect_list}")
                except Exception as e:
                    # Fallback to hardcoded list if method not available
                    effect_list = ["none", "rainbow", "chase", "fade", "strobe", "color_wipe", "theater_chase", "rainbow_cycle"]
                    print(f"✗ Failed to get effects from LED controller, using fallback: {e}")
            else:
                print("✗ No LED controller available, using fallback effects")
                effect_list = ["none", "rainbow", "chase", "fade", "strobe", "color_wipe", "theater_chase", "rainbow_cycle"]
            
            discovery_payload = {
                "name": f"WS2812B Strip",
                "unique_id": device_id,
                "object_id": device_id.lower().replace("-", "_"),
                "command_topic": ha_topics['command'],
                "state_topic": ha_topics['state'],
                "availability_topic": ha_topics['availability'],
                "payload_available": "online",
                "payload_not_available": "offline",
                "schema": "json",
                "brightness": True,
                "brightness_scale": 255,
                "supported_color_modes": supported_color_modes,
                "effect": True,
                "effect_list": effect_list,
                "optimistic": False,
                "device": {
                    "identifiers": [device_id],
                    "manufacturer": "WS2812B LED Controller",
                    "model": f"Pico W {led_mode or 'RGB'} Controller",
                    "name": f"WS2812B Strip ({device_id})",
                    "sw_version": "2.0"
                }
            }
            
            # Add configuration URL if connected to WiFi
            if self.wlan and self.wlan.isconnected():
                discovery_payload["device"]["configuration_url"] = f"http://{self.wlan.ifconfig()[0]}"
            
            # Publish discovery message
            discovery_json = json.dumps(discovery_payload)
            self.mqtt_client.publish(ha_topics['discovery'], discovery_json, retain=True)
            
            print(f"✓ Published Home Assistant discovery with {len(effect_list)} effects")
            if self.config['system'].get('debug', False):
                print(f"Discovery payload: {discovery_json}")
            
            # Publish initial state
            self.publish_ha_state()
            
            # Publish availability
            self.mqtt_client.publish(ha_topics['availability'], "online", retain=True)
            
        except Exception as e:
            print("✗ Failed to publish HA discovery:")
            print_exception(e)
    
    def _mqtt_callback(self, topic, msg):
        """Handle incoming MQTT messages"""
        try:
            topic_str = topic.decode('utf-8')
            topics = self.config['server']['mqtt']['topics']
            ha_topics = self._get_ha_topics()
            
            if self.config['system'].get('debug', False):
                print(f"MQTT: {topic_str} -> {len(msg)} bytes")
            
            if not self.led_controller:
                return
            
            if topic_str == topics['led_data']:
                # Raw LED data
                self.led_controller.process_led_data(msg)
            elif topic_str == topics['led_command']:
                # JSON command (legacy)
                self._process_mqtt_command(msg)
            elif topic_str == ha_topics['command']:
                # Home Assistant JSON command
                self._process_ha_command(msg)
                
        except Exception as e:
            print("✗ MQTT callback error:")
            print_exception(e)
    
    def _process_mqtt_command(self, msg):
        """Process MQTT command messages"""
        try:
            command = json.loads(msg.decode('utf-8'))
            
            if command.get('action') == 'fill':
                color = command.get('color', [0, 0, 0])
                self.led_controller.fill_color(color)
                
            elif command.get('action') == 'clear':
                self.led_controller.clear()
                
            elif command.get('action') == 'brightness':
                brightness = command.get('value', 255)
                self.led_controller.set_brightness(brightness)
                
            elif command.get('action') == 'test':
                self.led_controller.startup_test()
                
        except Exception as e:
            print("✗ MQTT command error:")
            print_exception(e)
    
    def _process_ha_command(self, msg):
        """Process Home Assistant JSON commands"""
        try:
            command = json.loads(msg.decode('utf-8'))
            
            if self.config['system'].get('debug', False):
                print(f"HA Command: {command}")
            
            self.led_controller.process_ha_command(command)
            # Use debounced state publishing to avoid flooding during rapid changes
            self._publish_ha_state_debounced()
                
        except Exception as e:
            print("✗ HA command error:")
            print_exception(e)
    
    def publish_ha_state(self):
        """Publish current state to Home Assistant"""
        if not self.mqtt_client or not self.led_controller or not self.connected:
            return
            
        try:
            ha_topics = self._get_ha_topics()
            state_payload = self.led_controller.get_ha_state()
            
            # Add effect list to state for reference
            if hasattr(self.led_controller, 'get_available_effects'):
                state_payload["fx_list"] = self.led_controller.get_available_effects()
            
            state_json = json.dumps(state_payload)
            self.mqtt_client.publish(ha_topics['state'], state_json, retain=True)
            
            if self.config['system'].get('debug', False):
                print(f"Published HA state: {state_payload}")
            
        except Exception as e:
            self.connected = False  # Mark as disconnected on publish error
            if self.config['system'].get('debug', False):
                print("HA state publish error:")
                print_exception(e)
    
    def _publish_ha_state_debounced(self):
        """Publish state with debouncing to avoid flooding during rapid changes"""
        current_time = time.time()
        if current_time - self.last_state_publish >= self.state_publish_debounce:
            self.last_state_publish = current_time
            self.publish_ha_state()
    
    def republish_discovery(self):
        """Re-publish Home Assistant discovery (useful when effects are updated)"""
        if self.connected:
            self._publish_ha_discovery()
    
    def publish_status(self):
        """Publish status message via MQTT"""
        if not self.mqtt_client or not self.connected:
            return
            
        try:
            topics = self.config['server']['mqtt']['topics']
            if not topics.get('status'):
                return
                
            status_msg = json.dumps({
                "status": "online",
                "uptime": time.time(),
                "led_count": self.config['led']['count'],
                "led_mode": self.config['led']['mode'],
                "wifi_rssi": self.wlan.status('rssi') if hasattr(self.wlan, 'status') else 'unknown',
                "protocols": {
                    "udp": self.config['server']['udp']['enabled'],
                    "mqtt": self.config['server']['mqtt']['enabled']
                }
            })
            
            self.mqtt_client.publish(topics['status'], status_msg)
            
        except Exception as e:
            self.connected = False  # Mark as disconnected on publish error
            if self.config['system'].get('debug', False):
                print("Status publish error:")
                print_exception(e)
    
    def check_messages(self):
        """Check for incoming MQTT messages - process available messages efficiently"""
        if not self.mqtt_client:
            return
            
        # If not connected, try to reconnect periodically
        if not self.connected:
            current_time = time.time()
            if current_time - self.last_connection_attempt > self.connection_retry_interval:
                self.last_connection_attempt = current_time
                if self.config['system'].get('debug', False):
                    print("Attempting MQTT reconnection...")
                self._connect_mqtt()
            return
        
        # Check for messages if connected - process efficiently without loops
        try:
            self.mqtt_client.check_msg()
        except OSError as e:
            # Connection lost or no data available
            if str(e) != "-1":  # -1 means no data, other errors are real connection issues
                self.connected = False
                if self.config['system'].get('debug', False):
                    print(f"MQTT connection lost: {e}")
        except Exception as e:
            # Other MQTT errors
            self.connected = False
            if self.config['system'].get('debug', False):
                print("MQTT error:")
                print_exception(e)
    
    def cleanup(self):
        """Cleanup MQTT resources"""
        if self.mqtt_client:
            try:
                # Publish offline status
                topics = self.config['server']['mqtt']['topics']
                if topics.get('status'):
                    offline_msg = json.dumps({"status": "offline", "timestamp": time.time()})
                    self.mqtt_client.publish(topics['status'], offline_msg)
                
                # Publish Home Assistant offline status
                ha_topics = self._get_ha_topics()
                self.mqtt_client.publish(ha_topics['availability'], "offline", retain=True)
                
                self.mqtt_client.disconnect()
            except:
                pass
            self.mqtt_client = None
