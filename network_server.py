"""
Network Streaming Server for SyncWave
Enables multi-room audio streaming over WiFi/LAN
"""

import socket
import threading
import json
import time
import logging
from zeroconf import ServiceInfo, Zeroconf
import numpy as np
import struct

logger = logging.getLogger(__name__)

class NetworkServer:
    """
    Server that broadcasts audio to multiple network clients
    """
    
    def __init__(self, port=5555):
        self.port = port
        self.is_running = False
        self.clients = []  # List of connected client sockets
        self.client_info = {}  # Client metadata
        self.server_socket = None
        self.accept_thread = None
        self.zeroconf = None
        self.service_info = None
        self.lock = threading.Lock()
        
    def start(self, server_name="SyncWave Server"):
        """Start the network server"""
        try:
            # Create TCP server socket
            self.server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            self.server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
            self.server_socket.bind(('0.0.0.0', self.port))
            self.server_socket.listen(10)
            
            self.is_running = True
            
            # Start accepting connections
            self.accept_thread = threading.Thread(target=self._accept_connections)
            self.accept_thread.daemon = True
            self.accept_thread.start()
            
            # Register mDNS service for discovery
            self._register_service(server_name)
            
            local_ip = self._get_local_ip()
            logger.info(f"Network server started on {local_ip}:{self.port}")
            
            return True, local_ip
            
        except Exception as e:
            logger.error(f"Failed to start server: {e}")
            return False, None
    
    def stop(self):
        """Stop the network server"""
        self.is_running = False
        
        # Close all client connections
        with self.lock:
            for client in self.clients:
                try:
                    client.close()
                except:
                    pass
            self.clients.clear()
            self.client_info.clear()
        
        # Close server socket
        if self.server_socket:
            try:
                self.server_socket.close()
            except:
                pass
        
        # Unregister mDNS service
        self._unregister_service()
        
        logger.info("Network server stopped")
    
    def _get_local_ip(self):
        """Get local IP address"""
        try:
            s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
            s.connect(("8.8.8.8", 80))
            ip = s.getsockname()[0]
            s.close()
            return ip
        except:
            return "127.0.0.1"
    
    def _register_service(self, server_name):
        """Register mDNS service for discovery"""
        try:
            self.zeroconf = Zeroconf()
            local_ip = self._get_local_ip()
            
            # Convert IP to bytes
            ip_bytes = socket.inet_aton(local_ip)
            
            self.service_info = ServiceInfo(
                "_syncwave._tcp.local.",
                f"{server_name}._syncwave._tcp.local.",
                addresses=[ip_bytes],
                port=self.port,
                properties={
                    'version': '3.0',
                    'name': server_name
                }
            )
            
            self.zeroconf.register_service(self.service_info)
            logger.info(f"mDNS service registered: {server_name}")
            
        except Exception as e:
            logger.error(f"Failed to register mDNS service: {e}")
    
    def _unregister_service(self):
        """Unregister mDNS service"""
        if self.zeroconf and self.service_info:
            try:
                self.zeroconf.unregister_service(self.service_info)
                self.zeroconf.close()
            except:
                pass
    
    def _accept_connections(self):
        """Accept incoming client connections"""
        while self.is_running:
            try:
                client_socket, address = self.server_socket.accept()
                
                logger.info(f"New client connected: {address}")
                
                # Add to clients list
                with self.lock:
                    self.clients.append(client_socket)
                    self.client_info[client_socket] = {
                        'address': address,
                        'connected_at': time.time(),
                        'name': f"Client {address[0]}"
                    }
                
                # Start thread to handle client
                client_thread = threading.Thread(
                    target=self._handle_client,
                    args=(client_socket,)
                )
                client_thread.daemon = True
                client_thread.start()
                
            except Exception as e:
                if self.is_running:
                    logger.error(f"Error accepting connection: {e}")
    
    def _handle_client(self, client_socket):
        """Handle individual client connection"""
        try:
            # Send welcome message
            welcome = {
                'type': 'welcome',
                'message': 'Connected to SyncWave Server',
                'server_time': time.time()
            }
            self._send_json(client_socket, welcome)
            
            # Keep connection alive and handle incoming messages
            while self.is_running:
                # Receive data from client (e.g., status updates, requests)
                try:
                    data = client_socket.recv(1024)
                    if not data:
                        break
                    
                    # Process client message
                    message = json.loads(data.decode('utf-8'))
                    self._handle_client_message(client_socket, message)
                    
                except socket.timeout:
                    continue
                except Exception as e:
                    logger.error(f"Error receiving from client: {e}")
                    break
                    
        except Exception as e:
            logger.error(f"Error handling client: {e}")
        finally:
            # Remove client
            with self.lock:
                if client_socket in self.clients:
                    self.clients.remove(client_socket)
                if client_socket in self.client_info:
                    del self.client_info[client_socket]
            
            try:
                client_socket.close()
            except:
                pass
            
            logger.info(f"Client disconnected")
    
    def _handle_client_message(self, client_socket, message):
        """Process messages from client"""
        msg_type = message.get('type')
        
        if msg_type == 'ping':
            # Respond to ping
            response = {'type': 'pong', 'time': time.time()}
            self._send_json(client_socket, response)
        
        elif msg_type == 'status':
            # Update client status
            with self.lock:
                if client_socket in self.client_info:
                    self.client_info[client_socket].update(message.get('data', {}))
        
        elif msg_type == 'set_name':
            # Update client name
            with self.lock:
                if client_socket in self.client_info:
                    self.client_info[client_socket]['name'] = message.get('name', 'Unknown')
    
    def _send_json(self, client_socket, data):
        """Send JSON data to client"""
        try:
            json_data = json.dumps(data).encode('utf-8')
            client_socket.sendall(json_data + b'\n')
        except Exception as e:
            logger.error(f"Error sending JSON: {e}")
    
    def broadcast_audio(self, audio_data):
        """
        Broadcast audio data to all connected clients
        
        Args:
            audio_data: bytes or numpy array of audio samples
        """
        if not self.clients:
            return
        
        # Convert to bytes if numpy array
        if isinstance(audio_data, np.ndarray):
            audio_bytes = audio_data.tobytes()
        else:
            audio_bytes = audio_data
        
        # Create packet: [size (4 bytes)][audio data]
        packet = struct.pack('I', len(audio_bytes)) + audio_bytes
        
        # Send to all clients
        with self.lock:
            disconnected = []
            for client in self.clients:
                try:
                    client.sendall(packet)
                except Exception as e:
                    logger.error(f"Error broadcasting to client: {e}")
                    disconnected.append(client)
            
            # Remove disconnected clients
            for client in disconnected:
                if client in self.clients:
                    self.clients.remove(client)
                if client in self.client_info:
                    del self.client_info[client]
                try:
                    client.close()
                except:
                    pass
    
    def get_connected_clients(self):
        """Get list of connected clients"""
        with self.lock:
            return [
                {
                    'name': info['name'],
                    'address': info['address'][0],
                    'connected_at': info['connected_at']
                }
                for info in self.client_info.values()
            ]
    
    def get_client_count(self):
        """Get number of connected clients"""
        with self.lock:
            return len(self.clients)


# Example usage
if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    
    server = NetworkServer(port=5555)
    success, ip = server.start("Test Server")
    
    if success:
        print(f"✅ Server started on {ip}:5555")
        print("Waiting for clients... (Press Ctrl+C to stop)")
        
        try:
            while True:
                time.sleep(1)
                clients = server.get_connected_clients()
                if clients:
                    print(f"\nConnected clients: {len(clients)}")
                    for client in clients:
                        print(f"  - {client['name']} ({client['address']})")
        except KeyboardInterrupt:
            print("\nStopping server...")
            server.stop()
    else:
        print("❌ Failed to start server")
