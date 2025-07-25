v0.2 
- OTA support, with ability to manage updates via MQTT
- BUG FIX: (Possibly not our fault) In HomeAssistant with RGBW lights, toggling light on/off with only white on always results in color brightness turning up
- BUG FIX: Effects don't seem to really be implemented properly yet

v0.3
- Handle multiple light fixtures via one controller
    - Split one WS2812B string of LEDs into multiple "fixtures"
    - Generate multiple WS2812B strings