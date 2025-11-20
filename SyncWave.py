import customtkinter as ctk
import threading
import tkinter as tk
from tkinter import messagebox
from PIL import Image
import os
import time

# Import our new engines
from audio_router import AppRouter
from audio_sync import SyncEngine
from calibration_engine import CalibrationEngine
from network_server import NetworkServer
from network_client import NetworkClient

ctk.set_appearance_mode("Dark")
ctk.set_default_color_theme("blue")

class TwinSyncApp(ctk.CTk):
    def __init__(self):
        super().__init__()

        self.title("SyncWave v3.0 - Network Edition")
        self.geometry("950x650")
        
        # Initialize Engines
        self.router = AppRouter()
        self.network_server = NetworkServer()
        self.sync_engine = SyncEngine(network_server=self.network_server)
        self.calibrator = CalibrationEngine()
        self.network_client = NetworkClient()
        
        # Store output strip references for calibration
        self.output_strips = []
        
        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(0, weight=1)

        # Tab View
        self.tab_view = ctk.CTkTabview(self)
        self.tab_view.grid(row=0, column=0, padx=20, pady=20, sticky="nsew")
        
        self.tab_matrix = self.tab_view.add("Matrix Routing")
        self.tab_sync = self.tab_view.add("Multi-Sync Broadcast")
        self.tab_network = self.tab_view.add("Network Streaming")
        
        self._setup_matrix_tab()
        self._setup_sync_tab()
        self._setup_network_tab()
        
        # Initial device population
        self._refresh_sync_devices()
        
        # Start background refresh
        self.after(2000, self._refresh_data)

    def _setup_matrix_tab(self):
        # Header
        header = ctk.CTkLabel(self.tab_matrix, text="Application Audio Routing", font=("Roboto", 20, "bold"))
        header.pack(pady=10)
        
        desc = ctk.CTkLabel(self.tab_matrix, text="Route specific apps to specific devices (e.g. YouTube -> Headphones 1)")
        desc.pack(pady=5)
        
        # Scrollable Frame for Apps
        self.app_list_frame = ctk.CTkScrollableFrame(self.tab_matrix, label_text="Running Applications")
        self.app_list_frame.pack(fill="both", expand=True, padx=10, pady=10)
        
        # Refresh Button
        refresh_btn = ctk.CTkButton(self.tab_matrix, text="Refresh Apps", command=self._refresh_matrix_list)
        refresh_btn.pack(pady=10)

    def _setup_sync_tab(self):
        # Header
        header = ctk.CTkLabel(self.tab_sync, text="Multi-Device Sync", font=("Roboto", 20, "bold"))
        header.pack(pady=10)
        
        desc = ctk.CTkLabel(self.tab_sync, text="Broadcast one source to multiple devices with delay compensation")
        desc.pack(pady=5)
        
        # Input Selection
        input_frame = ctk.CTkFrame(self.tab_sync)
        input_frame.pack(fill="x", padx=10, pady=10)
        
        ctk.CTkLabel(input_frame, text="Input Source:").pack(side="left", padx=10)
        self.input_combo = ctk.CTkComboBox(input_frame, values=["Scanning..."])
        self.input_combo.pack(side="left", fill="x", expand=True, padx=10)
        
        # Start/Stop
        self.sync_btn = ctk.CTkButton(input_frame, text="Start Sync", command=self._toggle_sync)
        self.sync_btn.pack(side="right", padx=10)
        
        # Output List
        self.output_list_frame = ctk.CTkScrollableFrame(self.tab_sync, label_text="Output Devices")
        self.output_list_frame.pack(fill="both", expand=True, padx=10, pady=10)
        
        # Add Output Button
        add_btn = ctk.CTkButton(self.tab_sync, text="Add Output Device", command=self._add_output_strip)
        add_btn.pack(pady=10)

    def _setup_network_tab(self):
        # Header
        header = ctk.CTkLabel(self.tab_network, text="Network Streaming 🌐", font=("Roboto", 20, "bold"))
        header.pack(pady=10)
        
        desc = ctk.CTkLabel(self.tab_network, text="Stream audio over WiFi to other devices")
        desc.pack(pady=5)
        
        # Mode Selection
        mode_frame = ctk.CTkFrame(self.tab_network)
        mode_frame.pack(fill="x", padx=10, pady=10)
        
        ctk.CTkLabel(mode_frame, text="Mode:", font=("Roboto", 14, "bold")).pack(side="left", padx=10)
        
        self.network_mode = ctk.StringVar(value="server")
        server_radio = ctk.CTkRadioButton(mode_frame, text="Host Server", 
                                          variable=self.network_mode, value="server",
                                          command=self._on_network_mode_change)
        server_radio.pack(side="left", padx=10)
        
        client_radio = ctk.CTkRadioButton(mode_frame, text="Connect as Client", 
                                          variable=self.network_mode, value="client",
                                          command=self._on_network_mode_change)
        client_radio.pack(side="left", padx=10)
        
        # Server Panel
        self.server_panel = ctk.CTkFrame(self.tab_network)
        self.server_panel.pack(fill="both", expand=True, padx=10, pady=10)
        
        # Server Controls
        server_control_frame = ctk.CTkFrame(self.server_panel)
        server_control_frame.pack(fill="x", padx=10, pady=10)
        
        self.server_name_entry = ctk.CTkEntry(server_control_frame, placeholder_text="Server Name")
        self.server_name_entry.insert(0, "My SyncWave Server")
        self.server_name_entry.pack(side="left", padx=5)
        
        self.start_server_btn = ctk.CTkButton(server_control_frame, text="Start Server", 
                                              command=self._toggle_server)
        self.start_server_btn.pack(side="left", padx=5)
        
        # Server Info
        self.server_info_label = ctk.CTkLabel(self.server_panel, text="Server not running", 
                                              font=("Roboto", 12))
        self.server_info_label.pack(pady=5)
        
        # QR Code placeholder (future feature)
        qr_frame = ctk.CTkFrame(self.server_panel)
        qr_frame.pack(pady=10)
        ctk.CTkLabel(qr_frame, text="📱 QR Code Connection (Coming Soon)", 
                    font=("Roboto", 12, "italic")).pack(pady=20)
        
        # Connected Clients List
        self.clients_frame = ctk.CTkScrollableFrame(self.server_panel, label_text="Connected Clients", height=200)
        self.clients_frame.pack(fill="both", expand=True, padx=10, pady=10)
        
        # Client Panel (hidden by default)
        self.client_panel = ctk.CTkFrame(self.tab_network)
        
        # Client Controls
        client_control_frame = ctk.CTkFrame(self.client_panel)
        client_control_frame.pack(fill="x", padx=10, pady=10)
        
        discover_btn = ctk.CTkButton(client_control_frame, text="🔍 Discover Servers", 
                                     command=self._discover_servers)
        discover_btn.pack(side="left", padx=5)
        
        self.refresh_servers_btn = ctk.CTkButton(client_control_frame, text="Refresh", 
                                                 command=self._discover_servers)
        self.refresh_servers_btn.pack(side="left", padx=5)
        
        # Available Servers List
        self.servers_frame = ctk.CTkScrollableFrame(self.client_panel, label_text="Available Servers", height=200)
        self.servers_frame.pack(fill="both", expand=True, padx=10, pady=10)
        
        # Connection Status
        self.client_status_label = ctk.CTkLabel(self.client_panel, text="Not connected", 
                                                font=("Roboto", 12))
        self.client_status_label.pack(pady=5)
        
        # Client Output Device Selection
        client_output_frame = ctk.CTkFrame(self.client_panel)
        client_output_frame.pack(fill="x", padx=10, pady=10)
        
        ctk.CTkLabel(client_output_frame, text="Output Device:").pack(side="left", padx=5)
        
        devices = self.router.get_audio_devices()
        device_names = [d['name'] for d in devices] if devices else ["No devices"]
        self.client_output_combo = ctk.CTkComboBox(client_output_frame, values=device_names, width=300)
        self.client_output_combo.pack(side="left", padx=5)
        
        # Show server panel by default
        self._on_network_mode_change()
    
    def _on_network_mode_change(self):
        """Switch between server and client modes"""
        mode = self.network_mode.get()
        
        if mode == "server":
            self.server_panel.pack(fill="both", expand=True, padx=10, pady=10)
            self.client_panel.pack_forget()
        else:
            self.server_panel.pack_forget()
            self.client_panel.pack(fill="both", expand=True, padx=10, pady=10)
    
    def _toggle_server(self):
        """Start/stop network server"""
        if not self.network_server.is_running:
            server_name = self.server_name_entry.get() or "SyncWave Server"
            success, ip = self.network_server.start(server_name)
            
            if success:
                self.start_server_btn.configure(text="Stop Server", fg_color="red")
                self.server_info_label.configure(text=f"✅ Server running on {ip}:5555", 
                                                text_color="green")
                # Start updating client list
                self._update_clients_list()
            else:
                messagebox.showerror("Error", "Failed to start server")
        else:
            self.network_server.stop()
            self.start_server_btn.configure(text="Start Server", fg_color="blue")
            self.server_info_label.configure(text="Server stopped", text_color="gray")
            # Clear clients list
            for widget in self.clients_frame.winfo_children():
                widget.destroy()
    
    def _update_clients_list(self):
        """Update list of connected clients"""
        if not self.network_server.is_running:
            return
        
        # Clear current list
        for widget in self.clients_frame.winfo_children():
            widget.destroy()
        
        # Get clients
        clients = self.network_server.get_connected_clients()
        
        if clients:
            for client in clients:
                client_row = ctk.CTkFrame(self.clients_frame)
                client_row.pack(fill="x", pady=2)
                
                ctk.CTkLabel(client_row, text=f"👤 {client['name']}", width=200, anchor="w").pack(side="left", padx=5)
                ctk.CTkLabel(client_row, text=client['address'], width=150, anchor="w").pack(side="left", padx=5)
                
                # Connection time
                elapsed = time.time() - client['connected_at']
                ctk.CTkLabel(client_row, text=f"{int(elapsed)}s ago").pack(side="right", padx=5)
        else:
            ctk.CTkLabel(self.clients_frame, text="No clients connected", 
                        font=("Roboto", 12, "italic"), text_color="gray").pack(pady=20)
        
        # Schedule next update
        self.after(2000, self._update_clients_list)
    
    def _discover_servers(self):
        """Discover available servers on network"""
        self.client_status_label.configure(text="🔍 Discovering servers...", text_color="blue")
        
        # Clear current list
        for widget in self.servers_frame.winfo_children():
            widget.destroy()
        
        def discover_thread():
            servers = self.network_client.discover_servers(timeout=3)
            
            # Update UI
            self.after(0, lambda: self._show_discovered_servers(servers))
        
        threading.Thread(target=discover_thread, daemon=True).start()
    
    def _show_discovered_servers(self, servers):
        """Display discovered servers"""
        # Clear list
        for widget in self.servers_frame.winfo_children():
            widget.destroy()
        
        if servers:
            self.client_status_label.configure(text=f"✅ Found {len(servers)} server(s)", 
                                              text_color="green")
            
            for server in servers:
                server_row = ctk.CTkFrame(self.servers_frame)
                server_row.pack(fill="x", pady=5)
                
                info_frame = ctk.CTkFrame(server_row)
                info_frame.pack(side="left", fill="x", expand=True, padx=5)
                
                ctk.CTkLabel(info_frame, text=f"🖥️ {server['name']}", 
                           font=("Roboto", 14, "bold"), anchor="w").pack(anchor="w")
                ctk.CTkLabel(info_frame, text=f"{server['address']}:{server['port']}", 
                           font=("Roboto", 10), anchor="w").pack(anchor="w")
                
                connect_btn = ctk.CTkButton(server_row, text="Connect", 
                                           command=lambda s=server: self._connect_to_server(s))
                connect_btn.pack(side="right", padx=5)
        else:
            self.client_status_label.configure(text="❌ No servers found", text_color="red")
            ctk.CTkLabel(self.servers_frame, text="No servers found on network\n\nMake sure a server is running", 
                        font=("Roboto", 12, "italic"), text_color="gray").pack(pady=20)
    
    def _connect_to_server(self, server):
        """Connect to a server"""
        self.client_status_label.configure(text=f"🔗 Connecting to {server['name']}...", 
                                          text_color="blue")
        
        def connect_thread():
            success = self.network_client.connect(server['address'], server['port'])
            
            if success:
                # Get selected output device
                device_text = self.client_output_combo.get()
                devices = self.router.get_audio_devices()
                device_index = None
                for dev in devices:
                    if dev['name'] in device_text:
                        device_index = dev['index']
                        break
                
                # Start playback
                self.network_client.start_playback(device_index=device_index)
                
                self.after(0, lambda: self.client_status_label.configure(
                    text=f"✅ Connected to {server['name']} - Playing audio", 
                    text_color="green"
                ))
            else:
                self.after(0, lambda: self.client_status_label.configure(
                    text="❌ Connection failed", 
                    text_color="red"
                ))
        
        threading.Thread(target=connect_thread, daemon=True).start()

    def _refresh_data(self):
        # Periodic refresh logic
        self.after(5000, self._refresh_data)

    def _refresh_sync_devices(self):
        """Populate input device dropdown with available sources"""
        devices = self.sync_engine.get_devices()
        # Filter for input devices and loopback devices
        input_devices = [f"{d['name']} (Index: {d['index']})" 
                        for d in devices 
                        if d['max_input'] > 0 or d.get('is_loopback', False)]
        
        if input_devices:
            self.input_combo.configure(values=input_devices)
            self.input_combo.set(input_devices[0])  # Set first as default
        else:
            self.input_combo.configure(values=["No input devices found"])
            self.input_combo.set("No input devices found")

    def _refresh_matrix_list(self):
        # Clear current list
        for widget in self.app_list_frame.winfo_children():
            widget.destroy()
            
        # Get Apps
        apps = self.router.get_active_apps()
        devices = self.router.get_audio_devices() # Need to implement this in router
        device_names = [d['name'] for d in devices] if devices else ["Default Device"]
        
        for app in apps:
            row = ctk.CTkFrame(self.app_list_frame)
            row.pack(fill="x", pady=5)
            
            ctk.CTkLabel(row, text=app['name'], width=150, anchor="w").pack(side="left", padx=10)
            
            # Device Selector
            combo = ctk.CTkComboBox(row, values=device_names, 
                                    command=lambda choice, pid=app['pid']: self._on_app_device_change(pid, choice))
            combo.pack(side="right", padx=10)

    def _on_app_device_change(self, pid, device_name):
        print(f"Changing PID {pid} to {device_name}")
        # self.router.set_app_device(pid, device_id)

    def _add_output_strip(self):
        # Add a row to Sync Tab
        row = ctk.CTkFrame(self.output_list_frame)
        row.pack(fill="x", pady=5)
        
        # Get real output devices
        devices = self.router.get_audio_devices()
        device_names = [d['name'] for d in devices] if devices else ["No devices found"]
        
        # Device Selector
        device_combo = ctk.CTkComboBox(row, values=device_names, width=250)
        device_combo.pack(side="left", padx=5)
        
        # Volume Label
        volume_label = ctk.CTkLabel(row, text="Vol: 100%", width=70)
        volume_label.pack(side="left", padx=5)
        
        # Volume Slider
        def on_volume_change(value):
            volume_label.configure(text=f"Vol: {int(value)}%")
        
        volume_slider = ctk.CTkSlider(row, from_=0, to=100, command=on_volume_change, width=120)
        volume_slider.set(100)  # Default 100%
        volume_slider.pack(side="left", fill="x", expand=True, padx=5)
        
        # Delay Label
        ctk.CTkLabel(row, text="Delay:").pack(side="left", padx=5)
        
        delay_label = ctk.CTkLabel(row, text="0 ms", width=60)
        delay_label.pack(side="left", padx=2)
        
        # Delay Slider (0-2000ms)
        def on_delay_change(value):
            delay_label.configure(text=f"{int(value)} ms")
        
        delay_slider = ctk.CTkSlider(row, from_=0, to=2000, command=on_delay_change, width=100)
        delay_slider.set(0)
        delay_slider.pack(side="left", padx=5)
        
        # Calibrate Button
        def calibrate_this_device():
            self._calibrate_output_device(device_combo, delay_slider, delay_label)
        
        calibrate_btn = ctk.CTkButton(row, text="📏 Cal", width=60, 
                                       command=calibrate_this_device)
        calibrate_btn.pack(side="left", padx=5)
        
        # Remove Button
        ctk.CTkButton(row, text="X", width=30, fg_color="red", 
                     command=lambda: self._remove_output_strip(row)).pack(side="right", padx=5)
        
        # Store reference
        strip_data = {
            'frame': row,
            'device_combo': device_combo,
            'volume_slider': volume_slider,
            'volume_label': volume_label,
            'delay_slider': delay_slider,
            'delay_label': delay_label,
            'calibrate_btn': calibrate_btn
        }
        self.output_strips.append(strip_data)
    
    def _remove_output_strip(self, row):
        """Remove an output strip"""
        # Remove from strips list
        self.output_strips = [s for s in self.output_strips if s['frame'] != row]
        # Destroy the frame
        row.destroy()
    
    def _calibrate_output_device(self, device_combo, delay_slider, delay_label):
        """Calibrate a specific output device"""
        device_text = device_combo.get()
        
        # Extract device index
        devices = self.router.get_audio_devices()
        device_index = None
        for dev in devices:
            if dev['name'] in device_text:
                device_index = dev['index']
                break
        
        if device_index is None:
            messagebox.showerror("Error", "Please select a valid device")
            return
        
        # Show calibration dialog
        calibration_window = ctk.CTkToplevel(self)
        calibration_window.title("Auto-Calibration")
        calibration_window.geometry("400x200")
        calibration_window.transient(self)
        calibration_window.grab_set()
        
        status_label = ctk.CTkLabel(calibration_window, text="Starting calibration...", 
                                     font=("Roboto", 14))
        status_label.pack(pady=20)
        
        progress_label = ctk.CTkLabel(calibration_window, text="", 
                                       font=("Roboto", 12))
        progress_label.pack(pady=10)
        
        # Run calibration in thread
        def run_calibration():
            def callback(message):
                progress_label.configure(text=message)
                self.update()
            
            delay, confidence = self.calibrator.calibrate_device(
                device_index,
                use_loopback=True,
                callback=callback
            )
            
            if delay is not None and confidence > 0.1:
                # Update delay slider
                delay_slider.set(delay)
                delay_label.configure(text=f"{int(delay)} ms")
                
                status_label.configure(text=f"✅ Success! Delay: {delay:.1f}ms", 
                                       text_color="green")
                progress_label.configure(text=f"Confidence: {confidence:.1%}")
            else:
                status_label.configure(text="❌ Calibration failed", 
                                       text_color="red")
                progress_label.configure(text="Could not detect delay. Try adjusting manually.")
            
            # Close button
            close_btn = ctk.CTkButton(calibration_window, text="Close", 
                                      command=calibration_window.destroy)
            close_btn.pack(pady=20)
        
        # Start calibration thread
        import threading
        cal_thread = threading.Thread(target=run_calibration)
        cal_thread.start()

    def _toggle_sync(self):
        print("Toggle Sync clicked!")
        if not self.sync_engine.is_running:
            # Get selected input device
            input_text = self.input_combo.get()
            print(f"Input text: {input_text}")
            
            # Check if this is a WASAPI Loopback device (Stereo Mix)
            is_loopback = "Stereo Mix" in input_text or "Loopback" in input_text or "WASAPI" in input_text
            
            # Extract index from text like "Stereo Mix (Index: 18)"
            try:
                input_index = int(input_text.split("Index: ")[1].rstrip(")"))
                print(f"Input index: {input_index}, Is Loopback: {is_loopback}")
            except Exception as e:
                print(f"Error parsing input: {e}")
                messagebox.showerror("Error", "Please select a valid input device")
                return
            
            # Get selected output devices with their volumes and delays
            output_indices = []
            volumes = []
            delays = []
            
            for strip in self.output_strips:
                device_combo = strip['device_combo']
                volume_slider = strip['volume_slider']
                delay_slider = strip['delay_slider']
                
                output_text = device_combo.get()
                print(f"Output text: {output_text}")
                
                # Extract device name and look up its index
                devices = self.router.get_audio_devices()
                for dev in devices:
                    if dev['name'] in output_text:
                        output_indices.append(dev['index'])
                        volumes.append(int(volume_slider.get()))
                        delays.append(int(delay_slider.get()))
                        print(f"Added output: index={dev['index']}, volume={volumes[-1]}%, delay={delays[-1]}ms")
                        break
            
            # Remove duplicates
            output_indices = list(dict.fromkeys(output_indices))
            print(f"Total unique output indices: {output_indices}")
            
            if not output_indices:
                messagebox.showerror("Error", "Please add at least one output device")
                return
            
            # Start sync with correct devices, volumes, and delays
            print(f"Starting sync: Input={input_index}, Outputs={output_indices}, Volumes={volumes}, Delays={delays}, UseLoopback={is_loopback}")
            try:
                self.sync_engine.start(input_index, output_indices, use_loopback=is_loopback, 
                                       volumes=volumes, delays=delays)
                self.sync_btn.configure(text="Stop Sync", fg_color="red")
                print("Sync started successfully!")
            except Exception as e:
                print(f"Error starting sync: {e}")
                messagebox.showerror("Error", f"Failed to start sync: {e}")
        else:
            print("Stopping sync...")
            self.sync_engine.stop()
            self.sync_btn.configure(text="Start Sync", fg_color="blue")
            print("Sync stopped.")

if __name__ == "__main__":
    app = TwinSyncApp()
    app.mainloop()
