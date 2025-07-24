import socket

try:
    from sys import print_exception
except ImportError:
    import traceback
    def print_exception(exc):
        traceback.print_exc()


class UDPServer:
    def __init__(self, config, wlan):
        self.config = config
        self.wlan = wlan
        self.udp_sock = None
        self.expected_packet_size = 0
    
    def setup(self, expected_packet_size):
        """Setup UDP server for receiving LED data"""
        if not self.config['server']['udp']['enabled']:
            return True
            
        self.expected_packet_size = expected_packet_size
        
        try:
            udp_config = self.config['server']['udp']
            server_ip = udp_config['ip']
            server_port = udp_config['port']
            timeout = udp_config.get('timeout', 1.0)
            
            self.udp_sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
            self.udp_sock.bind((server_ip, server_port))
            # Set a very small timeout for non-blocking behavior
            self.udp_sock.settimeout(0.001)  # 1ms timeout for responsive operation
            
            # Get actual IP for display
            if server_ip == "0.0.0.0" and self.wlan:
                display_ip = self.wlan.ifconfig()[0]
            else:
                display_ip = server_ip
            
            print(f"✓ UDP server listening on {display_ip}:{server_port}")
            return True
            
        except Exception as e:
            print("✗ Failed to setup UDP server:")
            print_exception(e)
            return False
    
    def receive_data(self):
        """Receive data from UDP socket"""
        if not self.udp_sock:
            return None, None
        
        try:
            data, addr = self.udp_sock.recvfrom(self.expected_packet_size + 100)
            return data, addr
        except OSError:
            # Timeout is expected
            return None, None
        except Exception as e:
            print("UDP receive error:")
            print_exception(e)
            return None, None
    
    def close(self):
        """Close UDP socket"""
        if self.udp_sock:
            try:
                self.udp_sock.close()
            except:
                pass
            self.udp_sock = None
