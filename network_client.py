"""
Network Client for SyncWave
Receives audio stream from network server and plays locally
"""

import socket
import threading
import json
import time
import logging
import struct
import numpy as np
import pyaudiowpatch as pyaudio
from zeroconf import ServiceBrowser, Zeroconf, ServiceStateChange

logger = logging.getLogger(__name__)

class NetworkClient:
    """
    Client that receives audio stream from server
    """
    
    def __init__(self):
        self.socket = None
        self.is_connected = False
        self.is_playing = False
        self.receive_thread = None
        self.play_thread = None
        self.audio_queue = []
        self.queue_lock = threading.Lock()
        self.p = pyaudio.PyAudio()
        self.output_stream = None
        self.server_info = None
        
    def discover_servers(self, timeout=5):
        """
        Discover available SyncWave servers on network
        
        Returns:
            list: List of discovered servers with their info
        """
        servers = []
        zeroconf_instance = Zeroconf()
        
        def on_service_state_change(zeroconf, service_type, name, state_change):
            if state_change is ServiceStateChange.Added:
                info = zeroconf.get_service_info(service_type, name)
                if info:
                    # Extract server info
                    address = socket.inet_ntoa(info.addresses[0])
                    port = info.port
                    props = {k.decode('utf-8'): v.decode('utf-8') 
                            for k, v in info.properties.items()}
                    
                    server = {
                        'name': props.get('name', name),
                        'address': address,
                        'port': port,
                        'version': props.get('version', 'unknown')
                    }
                    servers.append(server)
                    logger.info(f"Discovered server: {server['name']} at {address}:{port}")
        
        browser = ServiceBrowser(zeroconf_instance, "_syncwave._tcp.local.", 
                                handlers=[on_service_state_change])
        
        # Wait for discovery
        time.sleep(timeout)
        
        browser.cancel()
        zeroconf_instance.close()
        
        return servers
    
    def connect(self, host, port, client_name="SyncWave Client"):
        """Connect to server"""
        try:
            self.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            self.socket.connect((host, port))
            self.is_connected = True
            
            self.server_info = {'host': host, 'port': port}
            
            # Start receive thread
            self.receive_thread = threading.Thread(target=self._receive_loop)
            self.receive_thread.daemon = True
            self.receive_thread.start()
            
            # Send client name
            self._send_json({'type': 'set_name', 'name': client_name})
            
            logger.info(f"Connected to server {host}:{port}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to connect: {e}")
            self.is_connected = False
            return False
    
    def disconnect(self):
        """Disconnect from server"""
        self.is_connected = False
        self.stop_playback()
        
        if self.socket:
            try:
                self.socket.close()
            except:
                pass
        
        logger.info("Disconnected from server")
    
    def _send_json(self, data):
        """Send JSON message to server"""
        if not self.is_connected:
            return
        
        try:
            json_data = json.dumps(data).encode('utf-8')
            self.socket.sendall(json_data + b'\n')
        except Exception as e:
            logger.error(f"Error sending JSON: {e}")
    
    def _receive_loop(self):
        """Receive data from server"""
        buffer = b''
        
        while self.is_connected:
            try:
                # Receive data
                data = self.socket.recv(4096)
                if not data:
                    logger.warning("Server closed connection")
                    self.is_connected = False
                    break
                
                buffer += data
                
                # Check if it's JSON (control message)
                if b'\n' in buffer:
                    message_end = buffer.index(b'\n')
                    json_data = buffer[:message_end]
                    buffer = buffer[message_end + 1:]
                    
                    try:
                        message = json.loads(json_data.decode('utf-8'))
                        self._handle_server_message(message)
                    except:
                        # Not JSON, treat as audio data
                        pass
                
                # Check if it's audio packet [size][data]
                while len(buffer) >= 4:
                    # Read size
                    size = struct.unpack('I', buffer[:4])[0]
                    
                    if len(buffer) >= 4 + size:
                        # Extract audio data
                        audio_data = buffer[4:4+size]
                        buffer = buffer[4+size:]
                        
                        # Add to queue
                        with self.queue_lock:
                            self.audio_queue.append(audio_data)
                    else:
                        # Wait for more data
                        break
                        
            except Exception as e:
                if self.is_connected:
                    logger.error(f"Error receiving data: {e}")
                    self.is_connected = False
                break
    
    def _handle_server_message(self, message):
        """Handle control messages from server"""
        msg_type = message.get('type')
        
        if msg_type == 'welcome':
            logger.info(f"Server: {message.get('message')}")
        
        elif msg_type == 'pong':
            # Handle ping response
            pass
    
    def start_playback(self, device_index=None, sample_rate=44100, channels=2):
        """Start playing received audio"""
        if self.is_playing:
            return
        
        try:
            # Open output stream
            self.output_stream = self.p.open(
                format=pyaudio.paInt16,
                channels=channels,
                rate=sample_rate,
                output=True,
                output_device_index=device_index,
                frames_per_buffer=1024
            )
            
            self.is_playing = True
            
            # Start playback thread
            self.play_thread = threading.Thread(target=self._playback_loop)
            self.play_thread.daemon = True
            self.play_thread.start()
            
            logger.info("Playback started")
            
        except Exception as e:
            logger.error(f"Failed to start playback: {e}")
            self.is_playing = False
    
    def stop_playback(self):
        """Stop playing audio"""
        self.is_playing = False
        
        if self.output_stream:
            try:
                self.output_stream.stop_stream()
                self.output_stream.close()
            except:
                pass
            self.output_stream = None
        
        # Clear queue
        with self.queue_lock:
            self.audio_queue.clear()
        
        logger.info("Playback stopped")
    
    def _playback_loop(self):
        """Play audio from queue"""
        while self.is_playing:
            try:
                # Get audio from queue
                audio_data = None
                with self.queue_lock:
                    if self.audio_queue:
                        audio_data = self.audio_queue.pop(0)
                
                if audio_data:
                    # Play audio
                    self.output_stream.write(audio_data)
                else:
                    # No audio available, sleep briefly
                    time.sleep(0.001)
                    
            except Exception as e:
                logger.error(f"Error in playback loop: {e}")
                break
    
    def get_buffer_size(self):
        """Get current audio buffer size"""
        with self.queue_lock:
            return len(self.audio_queue)
    
    def cleanup(self):
        """Cleanup resources"""
        self.disconnect()
        try:
            self.p.terminate()
        except:
            pass


# Example usage
if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    
    client = NetworkClient()
    
    print("🔍 Discovering servers...")
    servers = client.discover_servers(timeout=3)
    
    if servers:
        print(f"\n✅ Found {len(servers)} server(s):")
        for i, server in enumerate(servers):
            print(f"  [{i}] {server['name']} - {server['address']}:{server['port']}")
        
        # Connect to first server
        choice = 0
        if len(servers) > 1:
            choice = int(input("\nSelect server (0-{}): ".format(len(servers)-1)))
        
        server = servers[choice]
        print(f"\n🔗 Connecting to {server['name']}...")
        
        if client.connect(server['address'], server['port']):
            print("✅ Connected!")
            
            # List audio devices
            p = pyaudio.PyAudio()
            print("\n🔊 Available output devices:")
            for i in range(p.get_device_count()):
                dev = p.get_device_info_by_index(i)
                if dev['maxOutputChannels'] > 0:
                    print(f"  [{i}] {dev['name']}")
            p.terminate()
            
            device = int(input("\nSelect output device: "))
            
            # Start playback
            client.start_playback(device_index=device)
            print("\n▶️ Playing... (Press Ctrl+C to stop)")
            
            try:
                while True:
                    time.sleep(1)
                    buffer_size = client.get_buffer_size()
                    print(f"\rBuffer: {buffer_size} packets", end='', flush=True)
            except KeyboardInterrupt:
                print("\n\n⏹️ Stopping...")
                client.cleanup()
        else:
            print("❌ Failed to connect")
    else:
        print("❌ No servers found")
        print("\nTry manual connection:")
        host = input("Server IP: ")
        port = int(input("Server Port (default 5555): ") or "5555")
        
        if client.connect(host, port):
            print("✅ Connected!")
            client.start_playback()
            
            try:
                while True:
                    time.sleep(1)
            except KeyboardInterrupt:
                client.cleanup()
