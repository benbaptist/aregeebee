#!/usr/bin/env python3
"""
LED Strip Controller - Simple UDP Client

This client sends LED data to the LED controller running on a Pico W using UDP.
All configuration is provided via command-line arguments using Click.

Features:
- UDP raw LED data transmission
- Support for both RGB and RGBW modes
- Command-line interface with Click
"""

import socket
import time
import click


class LEDClient:
    def __init__(self, target_ip, udp_port, led_count, led_mode):
        self.target_ip = target_ip
        self.udp_port = udp_port
        self.led_count = led_count
        self.led_mode = led_mode
        self.bytes_per_led = len(led_mode)
        
        # Initialize UDP socket
        self.udp_sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        
    def send_data(self, led_data):
        """
        Send LED data via UDP
        
        Args:
            led_data: List of tuples representing LED colors
                     Each tuple should have the same number of values as letters in led_mode
                     e.g., RGB: [(r,g,b), ...], RGBW: [(r,g,b,w), ...], WRGB: [(w,r,g,b), ...]
        """
        if len(led_data) != self.led_count:
            click.echo(f"Error: Expected {self.led_count} LEDs, got {len(led_data)}")
            return False
            
        # Convert to bytes
        data = bytearray()
        for led in led_data:
            if len(led) == self.bytes_per_led:
                data.extend(led)
            else:
                click.echo(f"Error: Each LED should have {self.bytes_per_led} values for {self.led_mode} mode, got {len(led)}")
                return False
        
        try:
            self.udp_sock.sendto(data, (self.target_ip, self.udp_port))
            click.echo(f"Sent {len(data)} bytes to {self.target_ip}:{self.udp_port}")
            return True
        except Exception as e:
            click.echo(f"Error sending UDP data: {e}")
            return False
    
    def fill_color(self, color):
        """Fill all LEDs with a single color"""
        led_data = [tuple(color)] * self.led_count
        return self.send_data(led_data)
    
    def clear_leds(self):
        """Clear all LEDs (turn off)"""
        led_data = [(0,) * self.bytes_per_led] * self.led_count
        return self.send_data(led_data)
    
    def close(self):
        """Close UDP socket"""
        self.udp_sock.close()


@click.group()
def cli():
    """LED Strip Controller - Simple UDP Client"""
    pass


@cli.command()
@click.option('--ip', required=True, help='Target IP address of the Pico W')
@click.option('--port', default=8000, help='UDP port (default: 8000)')
@click.option('--led-count', default=4, help='Number of LEDs (default: 4)')
@click.option('--led-mode', default='RGBW', help='LED mode/color order (e.g., RGB, RGBW, WRGB, GRB, etc.)')
@click.option('--r', default=255, help='Red value (0-255)')
@click.option('--g', default=0, help='Green value (0-255)')
@click.option('--b', default=0, help='Blue value (0-255)')
@click.option('--w', default=0, help='White value (0-255, for modes with W)')
def fill(ip, port, led_count, led_mode, r, g, b, w):
    """Fill all LEDs with a single color"""
    client = LEDClient(ip, port, led_count, led_mode)
    
    try:
        # Build color tuple based on the led_mode pattern
        color_map = {'R': r, 'G': g, 'B': b, 'W': w}
        color = []
        for channel in led_mode.upper():
            if channel in color_map:
                color.append(color_map[channel])
            else:
                click.echo(f"Warning: Unknown channel '{channel}' in led_mode '{led_mode}', using 0")
                color.append(0)
        
        click.echo(f"Filling {led_count} {led_mode} LEDs with color {color}")
        client.fill_color(color)
        
    finally:
        client.close()


@cli.command()
@click.option('--ip', required=True, help='Target IP address of the Pico W')
@click.option('--port', default=8000, help='UDP port (default: 8000)')
@click.option('--led-count', default=4, help='Number of LEDs (default: 4)')
@click.option('--led-mode', default='RGBW', help='LED mode/color order (e.g., RGB, RGBW, WRGB, GRB, etc.)')
def clear(ip, port, led_count, led_mode):
    """Clear all LEDs (turn off)"""
    client = LEDClient(ip, port, led_count, led_mode)
    
    try:
        click.echo(f"Clearing {led_count} {led_mode} LEDs")
        client.clear_leds()
        
    finally:
        client.close()


@cli.command()
@click.option('--ip', required=True, help='Target IP address of the Pico W')
@click.option('--port', default=8000, help='UDP port (default: 8000)')
@click.option('--led-count', default=4, help='Number of LEDs (default: 4)')
@click.option('--led-mode', default='RGBW', help='LED mode/color order (e.g., RGB, RGBW, WRGB, GRB, etc.)')
@click.option('--pattern', type=click.Choice(['rainbow', 'chase']), default='rainbow', help='Pattern to display')
@click.option('--duration', default=5.0, help='Duration in seconds (default: 5.0)')
def demo(ip, port, led_count, led_mode, pattern, duration):
    """Run a demo pattern"""
    client = LEDClient(ip, port, led_count, led_mode)
    
    try:
        click.echo(f"Running {pattern} pattern for {duration} seconds")
        
        if pattern == 'rainbow':
            # Define base colors in RGBW format
            base_colors = [
                {'R': 255, 'G': 0, 'B': 0, 'W': 0},    # Red
                {'R': 255, 'G': 165, 'B': 0, 'W': 0},  # Orange
                {'R': 255, 'G': 255, 'B': 0, 'W': 0},  # Yellow
                {'R': 0, 'G': 255, 'B': 0, 'W': 0},    # Green
                {'R': 0, 'G': 0, 'B': 255, 'W': 0},    # Blue
                {'R': 75, 'G': 0, 'B': 130, 'W': 0},   # Indigo
                {'R': 238, 'G': 130, 'B': 238, 'W': 0} # Violet
            ]
            
            # Convert colors to match the led_mode pattern and repeat to fill all LEDs
            rainbow_colors = []
            for i in range(led_count):
                # Cycle through base colors to fill all LEDs
                color_dict = base_colors[i % len(base_colors)]
                color_tuple = []
                for channel in led_mode.upper():
                    if channel in color_dict:
                        color_tuple.append(color_dict[channel])
                    else:
                        color_tuple.append(0)
                rainbow_colors.append(tuple(color_tuple))
            
            client.send_data(rainbow_colors)
            time.sleep(duration)
            
        elif pattern == 'chase':
            chase_duration = duration / (led_count * 2)
            for i in range(led_count * 2):
                led_data = [(0,) * len(led_mode)] * led_count
                if i < led_count:
                    # Create white chase based on led_mode pattern
                    white_values = []
                    for channel in led_mode.upper():
                        if channel in ['R', 'G', 'B']:
                            white_values.append(255)
                        else:  # W or other
                            white_values.append(0)
                    led_data[i] = tuple(white_values)
                
                client.send_data(led_data)
                time.sleep(chase_duration)
        
        # Clear LEDs at the end
        client.clear_leds()
        
    finally:
        client.close()


@cli.command()
@click.option('--ip', required=True, help='Target IP address of the Pico W')
@click.option('--port', default=8000, help='UDP port (default: 8000)')
@click.option('--led-count', default=4, help='Number of LEDs (default: 4)')
@click.option('--led-mode', default='RGBW', help='LED mode/color order (e.g., RGB, RGBW, WRGB, GRB, etc.)')
@click.argument('colors', nargs=-1, required=True)
def custom(ip, port, led_count, led_mode, colors):
    """Send custom colors to LEDs
    
    Colors should be provided as space-separated values.
    The number of values per LED matches the length of led_mode.
    For RGB mode: R G B R G B ... (3 values per LED)
    For RGBW mode: R G B W R G B W ... (4 values per LED)
    For WRGB mode: W R G B W R G B ... (4 values per LED)
    
    Example: python example.py custom --ip 192.168.1.100 --led-mode WRGB 0 255 0 0 0 0 255 0 0 0 0 255 255 255 255 255
    """
    client = LEDClient(ip, port, led_count, led_mode)
    
    try:
        values_per_led = len(led_mode)
        expected_values = led_count * values_per_led
        
        if len(colors) != expected_values:
            click.echo(f"Error: Expected {expected_values} color values ({led_count} LEDs × {values_per_led} values), got {len(colors)}")
            return
        
        # Convert string values to integers
        try:
            color_values = [int(c) for c in colors]
        except ValueError:
            click.echo("Error: All color values must be integers (0-255)")
            return
        
        # Validate range
        for val in color_values:
            if val < 0 or val > 255:
                click.echo("Error: All color values must be between 0 and 255")
                return
        
        # Group values into LED tuples
        led_data = []
        for i in range(0, len(color_values), values_per_led):
            led_data.append(tuple(color_values[i:i + values_per_led]))
        
        click.echo(f"Sending custom colors to {led_count} {led_mode} LEDs")
        client.send_data(led_data)
        
    finally:
        client.close()


if __name__ == "__main__":
    cli() 