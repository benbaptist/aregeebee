# AreGeeBee for Pico W

A modular MicroPython-based LED strip controller for Raspberry Pi Pico W that receives color data over WiFi via **UDP and MQTT protocols**. This enhanced version features a clean modular architecture, organized configuration, and **Home Assistant MQTT Discovery** integration.

## 🎯 Features

### Configuration & Setup
- **Auto-generates** `config.json` with sensible defaults
- Supports both **RGB** (3 bytes) and **RGBW** (4 bytes) LED modes
- **Clean structure** with logical sections (wifi, led, server, system)

### Communication Protocols

#### 1. UDP Protocol
- Raw binary LED data transmission
- High-performance for real-time applications
- Configurable IP/port binding

#### 2. MQTT Protocol
- **Raw Data Topic**: Binary LED data transmission  
- **Command Topic**: JSON-based commands (fill, clear, brightness, test)
- **Status Topic**: Real-time controller status publishing
- SSL/TLS support for secure connections
- Configurable QoS levels

### Operating Modes

#### 1. LED Tester Mode
- Tests LEDs incrementally starting from 1 LED
- Cycles through red, green, blue colors on each LED count
- Tests white color if in RGBW mode
- Automatically increments LED count and repeats
- Hard limit of 1000 LEDs before resetting back to 1

#### 2. Normal Operation Mode
- **LED Startup Test**: Configurable startup color sequence
- **WiFi Connection**: Auto-reconnection with configurable timeout
- **Dual Servers**: Simultaneous UDP and MQTT operation
- **Status Monitoring**: Periodic status publishing via MQTT
- **Error Recovery**: Automatic reconnection and error handling

## 📋 Hardware Requirements

- Raspberry Pi Pico W
- WS2812B/SK6812 LED strip
- Appropriate power supply for your LED strip
- Data line connected to the specified GPIO pin (default: GPIO 28)
- ???
- Profit

## ⚙️ Configuration

The controller will **automatically generate** a `config.json` file on first run. The controller will enter AP mode by default, so you can connect to its access point and play with it without using a network.

#### Color Channel Ordering (`mode`)
The `mode` setting controls the order of color channels sent to your LED strip:

- **`"RGB"`** - Standard Red, Green, Blue order
- **`"GRB"`** - Green, Red, Blue (most common for WS2812B strips)
- **`"BGR"`** - Blue, Green, Red  
- **`"RGBW"`** - Red, Green, Blue, White (most common for RGBW strips)
- **`"GRBW"`** - Green, Red, Blue, White
- **`"BGRW"`** - Blue, Green, Red, White

**🔧 Troubleshooting Colors:** If colors appear wrong (e.g., blue shows as green), try changing the mode. Most WS2812B strips use `"GRB"` ordering, but you never know in the wacky world of random Chinese-manufactured LED strips.

### Server Settings
```json
"server": {
  "protocols": ["udp", "mqtt"],
  "udp": {
    "enabled": true,
    "ip": "0.0.0.0",          // Bind IP (0.0.0.0 for all interfaces)
    "port": 8000,             // UDP port
    "timeout": 1.0            // Socket timeout
  },
  "mqtt": {
    "enabled": true,
    "broker": "192.168.1.100", // MQTT broker IP/hostname
    "port": 1883,             // MQTT port (1883=plain, 8883=SSL)
    "username": "",           // MQTT username (optional)
    "password": "",           // MQTT password (optional)
    "client_id": "pico-led-controller",
    "keepalive": 60,
    "ssl": false,             // Enable SSL/TLS
    "topics": {
      "led_data": "led/data",      // Raw LED data topic
      "led_command": "led/command", // JSON commands topic
      "status": "led/status"       // Status publishing topic
    },
    "qos": 0                 // MQTT QoS level (0, 1, or 2)
  }
}
```

### System Settings
```json
"system": {
  "led_tester_mode": false,   // Enable LED tester mode
  "debug": true,              // Enable debug output
  "status_interval": 30,      // Status publish interval (seconds)
  "memory_monitor": false     // Enable memory monitoring
}
```

## 🔧 Installation & Usage

### 1. Prepare Your Pico W

1. Flash MicroPython firmware (with wireless compatibility) onto your Pico W
2. Push this project to your Pico (better instructions to come later)

### 2. Hardware Connections

- Connect LED strip data line to GPIO 28 (or your configured pin)
- Connect LED strip ground to Pico W ground  
- Connect LED strip power to appropriate external power supply
- **Important**: Use external power for LED strips with more than a few LEDs

### 3. First Run

1. Reset your Pico W or run: `import main`
2. The controller will auto-generate `config.json`
3. Edit `config.json` with your WiFi and MQTT settings
4. Reset again to start with your configuration

## 📡 Sending LED Data

### Data Formats

#### UDP (Raw Binary)
Send UDP packets with raw LED data:
- **RGB Mode**: 3 bytes per LED (Red, Green, Blue)
- **RGBW Mode**: 4 bytes per LED (Red, Green, Blue, White)

#### MQTT Raw Data
Publish to `led/data` topic with same binary format as UDP.

#### MQTT JSON Commands
Publish to `led/command` topic with JSON commands:

```json
// Fill all LEDs with color
{"action": "fill", "color": [255, 0, 0, 0]}

// Clear all LEDs  
{"action": "clear"}

// Set brightness (0-255)
{"action": "brightness", "value": 128}

// Trigger startup test
{"action": "test"}
```

### Using the Enhanced Client

The included `clients/example.py` demonstrates both protocols:

```bash
# Install MQTT client library
pip install paho-mqtt

# Run the enhanced client
python3 clients/example.py
```

Features:
- Automatic protocol detection
- Interactive command mode
- Both UDP and MQTT examples
- Status monitoring

### Custom Client Examples

#### UDP Client (Compatible with v1.x)
```python
import socket

sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
led_data = [255, 0, 0,  0, 255, 0,  0, 0, 255]  # Red, Green, Blue LEDs
sock.sendto(bytes(led_data), ("192.168.1.100", 8000))
sock.close()
```

#### MQTT Client (Raw Data)
```python
import paho.mqtt.client as mqtt

client = mqtt.Client()
client.connect("192.168.1.100", 1883, 60)
led_data = bytes([255, 0, 0,  0, 255, 0,  0, 0, 255])
client.publish("led/data", led_data)
client.disconnect()
```

#### MQTT Client (JSON Commands)  
```python
import paho.mqtt.client as mqtt
import json

client = mqtt.Client()
client.connect("192.168.1.100", 1883, 60)

# Fill with red
client.publish("led/command", json.dumps({"action": "fill", "color": [255, 0, 0, 0]}))

# Set brightness to 50%
client.publish("led/command", json.dumps({"action": "brightness", "value": 128}))

client.disconnect()
```

## 🔍 Status Monitoring

Subscribe to the `led/status` topic to receive real-time status:

```json
{
  "status": "online",
  "uptime": 1234567,
  "led_count": 50,
  "led_mode": "RGB", 
  "wifi_rssi": -45,
  "protocols": {
    "udp": true,
    "mqtt": true
  }
}
```

## 🐛 Troubleshooting

### Configuration Issues
- **Missing config**: Controller auto-generates `config.json` on first run
- **Invalid settings**: Check debug output for validation errors

### WiFi Connection Issues
- Ensure WiFi credentials are correct in `config.json`
- Verify your WiFi network is 2.4GHz (Pico W doesn't support 5GHz)
- Check signal strength and range

### MQTT Issues
- **Library missing**: Make sure `umqtt/` folder is uploaded to Pico W
- **Connection failed**: Verify broker IP, port, and credentials
- **SSL issues**: For SSL, ensure broker supports TLS and certificates are valid
- **Topic permissions**: Check MQTT broker ACL settings

### LED Issues
- Verify power supply is adequate for your LED count
- Check data line connection to correct GPIO pin
- Ensure LED mode (RGB/RGBW) matches your strip type
- Try LED tester mode: set `"led_tester_mode": true` in config

### UDP Communication Issues
- Verify Pico W's IP address matches your client settings
- Check firewall settings on client device  
- Ensure packet size matches expected size for your LED count
- Monitor debug output for packet validation errors

##  Power Considerations

- Each LED can draw up to 60mA at full brightness
- For 50 RGB LEDs at full white: 50 × 3 × 60mA = 9A required
- Use appropriate external power supply for larger installations
- Consider power injection for strips longer than 5 meters

## 🏗️ Integration Examples

### Home Assistant
```yaml
# configuration.yaml
light:
  - platform: mqtt
    name: "Pico LED Strip"
    state_topic: "led/status"
    command_topic: "led/command"
    brightness_command_topic: "led/command"
    payload_on: '{"action": "fill", "color": [255, 255, 255, 0]}'
    payload_off: '{"action": "clear"}'
    brightness_command_template: '{"action": "brightness", "value": {{ brightness }}}'
```

### Node-RED
Use MQTT nodes to:
- Subscribe to `led/status` for monitoring
- Publish to `led/command` for control
- Create dashboard controls for colors and effects

### Custom Automation
Monitor status and send commands programmatically using any MQTT client library.

## 🏠 Home Assistant Integration

The controller now supports **Home Assistant MQTT Discovery**, which means your LED strip will automatically appear in Home Assistant without any manual configuration!

### How It Works

When the controller connects to your MQTT broker, it automatically:

1. **Publishes discovery messages** to Home Assistant-specific topics
2. **Registers as a light entity** with full color, brightness, and effect support
3. **Reports availability** so Home Assistant knows when the device is online/offline
4. **Responds to commands** sent through Home Assistant's interface

### Supported Features in Home Assistant

✅ **On/Off Control** - Turn your LED strip on and off  
✅ **Brightness Control** - Full 0-255 brightness range  
✅ **RGB Colors** - Full color wheel support for RGB mode  
✅ **RGBW Colors** - Separate white channel control for RGBW mode  
✅ **Effects** - 8 Built-in effects: None, Rainbow, Chase, Fade, Strobe, Color Wipe, Theater Chase, Rainbow Cycle  
✅ **State Feedback** - Real-time status updates  
✅ **Device Information** - Proper device registry integration  
✅ **Availability Status** - Shows online/offline status  

### Setup Instructions

1. **Configure MQTT in Home Assistant** (if not already done):
   ```yaml
   # configuration.yaml
   mqtt:
     broker: "your-mqtt-broker-ip"
     port: 1883
     username: "your-username"  # optional
     password: "your-password"  # optional
   ```

2. **Configure your LED controller** with the same MQTT broker settings in `config.json`

3. **Start the controller** - that's it! The device will automatically appear in Home Assistant. Bada-bing, bada-boom. And you know this wasn't generated with AI, because an AI would never write that, unless prompted. Nor this part either. Huzzah.

### Finding Your Device

After the controller connects:

1. Go to **Settings** → **Devices & Services** → **MQTT**
2. Look for "**WS2812B Strip (your-device-name)**"
3. The device will appear with a light entity that you can add to dashboards

### Manual Configuration (Alternative)

If you prefer manual configuration or the auto-discovery doesn't work, you can add this to your Home Assistant `configuration.yaml`:

```yaml
# For RGB Mode
mqtt:
  light:
    - name: "WS2812B LED Strip"
      schema: json
      unique_id: "pico-led-controller"
      command_topic: "homeassistant/light/pico-led-controller/set"
      state_topic: "homeassistant/light/pico-led-controller/state"
      availability_topic: "homeassistant/light/pico-led-controller/availability"
      brightness: true
      brightness_scale: 255
      supported_color_modes: ["rgb", "brightness"]
      effect: true
      effect_list: ["none", "rainbow", "chase", "fade", "strobe", "color_wipe", "theater_chase", "rainbow_cycle"]
      optimistic: false
      qos: 0

# For RGBW Mode  
mqtt:
  light:
    - name: "WS2812B LED Strip"
      schema: json
      unique_id: "pico-led-controller"
      command_topic: "homeassistant/light/pico-led-controller/set"
      state_topic: "homeassistant/light/pico-led-controller/state"
      availability_topic: "homeassistant/light/pico-led-controller/availability"
      brightness: true
      brightness_scale: 255
      supported_color_modes: ["rgbw", "brightness"]
      effect: true
      effect_list: ["none", "rainbow", "chase", "fade", "strobe", "color_wipe", "theater_chase", "rainbow_cycle"]
      optimistic: false
      qos: 0
```

### MQTT Topics Used

The controller uses these topics for Home Assistant integration:

- **Discovery**: `homeassistant/light/{client_id}/config`
- **Commands**: `homeassistant/light/{client_id}/set`
- **State**: `homeassistant/light/{client_id}/state`
- **Availability**: `homeassistant/light/{client_id}/availability`

Where `{client_id}` is your configured MQTT client ID (default: "pico-led-controller").

### Command Examples

You can also control the lights directly via MQTT:

```bash
# Turn on with red color
mosquitto_pub -h your-broker -t "homeassistant/light/pico-led-controller/set" \
  -m '{"state":"ON","color":{"r":255,"g":0,"b":0}}'

# Set brightness to 50%
mosquitto_pub -h your-broker -t "homeassistant/light/pico-led-controller/set" \
  -m '{"brightness":128}'

# Enable rainbow effect
mosquitto_pub -h your-broker -t "homeassistant/light/pico-led-controller/set" \
  -m '{"state":"ON","effect":"rainbow"}'

# Turn off
mosquitto_pub -h your-broker -t "homeassistant/light/pico-led-controller/set" \
  -m '{"state":"OFF"}'
```

### Troubleshooting Home Assistant Integration

**Device doesn't appear:**
- Check that MQTT discovery is enabled in Home Assistant
- Verify MQTT broker connection on both Home Assistant and the controller
- Look for errors in Home Assistant logs
- Restart Home Assistant if needed

**Commands don't work:**
- Enable debug mode in `config.json` to see incoming commands
- Check the MQTT logs in Home Assistant
- Verify the topics match your client ID

**State not updating:**
- Check network connectivity between devices
- Verify MQTT retain settings
- Look for MQTT connection errors in controller debug output

## 🎨 Available Effects

The controller now supports 8 built-in effects that can be selected through Home Assistant or MQTT commands:

### Basic Effects
- **none** - Solid color display (uses current color or white)
- **fade** - Displays at half brightness for a gentle fade effect

### Rainbow Effects  
- **rainbow** - Static rainbow pattern across all LEDs
- **rainbow_cycle** - Smoother rainbow effect using color wheel algorithm

### Movement Effects
- **chase** - Simple chase pattern with every 3rd LED illuminated  
- **theater_chase** - Theater-style chase effect using current color (or blue)
- **color_wipe** - Progressively fills LEDs one by one with current color (or red)

### Strobe Effect
- **strobe** - Flashing white strobe effect

### Effect Customization

Effects automatically adapt to your LED configuration:
- **RGB Mode**: Uses 3-channel colors (Red, Green, Blue)
- **RGBW Mode**: Uses 4-channel colors with dedicated white channel
- **Color Integration**: Effects like `theater_chase` and `color_wipe` use your current color setting
- **Brightness**: All effects respect the current brightness setting

### Controlling Effects

**Through Home Assistant:**
1. Select your LED device
2. Choose "Effect" from the control options  
3. Pick from the dropdown list of available effects

**Through MQTT:**
```json
{
  "state": "ON",
  "effect": "rainbow_cycle",
  "brightness": 200
}
```

**Through the Python Client:**
```python
client.set_effect("theater_chase")
client.turn_on(brightness=150, effect="rainbow")
```

## � Quick Start for Home Assistant

### Method 1: Automatic Configuration (Recommended)

1. **Run the configuration helper:**
   ```bash
   python configure_homeassistant.py
   ```
   This will guide you through setting up WiFi, MQTT, and LED parameters.

2. **Copy files to your Pico W:**
   - `config.json` (generated by the helper)
   - `main.py` and all Python files
   - `microdot/` and `umqtt/` directories

3. **Run on Pico W:**
   ```python
   import main
   ```

4. **Check Home Assistant:**
   - Go to Settings → Devices & Services → MQTT
   - Your LED strip should appear automatically!

### Method 2: Manual Configuration

1. **Edit `config.json`** with your settings:
   ```json
   {
     "wifi": {
       "ssid": "Your_WiFi_Name",
       "password": "Your_WiFi_Password"
     },
     "server": {
       "mqtt": {
         "enabled": true,
         "broker": "192.168.1.100",
         "client_id": "led-controller-001"
       }
     }
   }
   ```

2. **Follow steps 2-4 from Method 1**

### Testing Your Setup

Use the included client to test effects:
```bash
cd clients/
python homeassistant_example.py
```

This will let you manually test all effects and commands before using Home Assistant.

This project is open source and available under the MIT License.

## 🤝 Contributing

Contributions are welcome! Please feel free to submit issues, feature requests, or pull requests.

## 📞 Support

For support and questions:
1. Check the troubleshooting section above
2. Review the example configuration and client code
3. Enable debug mode for detailed logging
4. Submit an issue with your configuration and debug output 