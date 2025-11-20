import customtkinter as ctk
import threading
import tkinter as tk
from tkinter import messagebox
from PIL import Image
import os

# Import our new engines
from audio_router import AppRouter
from audio_sync import SyncEngine

ctk.set_appearance_mode("Dark")
ctk.set_default_color_theme("blue")

class TwinSyncApp(ctk.CTk):
    def __init__(self):
        super().__init__()

        self.title("SyncWave v2.0")
        self.geometry("900x600")
        
        # Initialize Engines
        self.router = AppRouter()
        self.sync_engine = SyncEngine()
        
        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(0, weight=1)

        # Tab View
        self.tab_view = ctk.CTkTabview(self)
        self.tab_view.grid(row=0, column=0, padx=20, pady=20, sticky="nsew")
        
        self.tab_matrix = self.tab_view.add("Matrix Routing")
        self.tab_sync = self.tab_view.add("Multi-Sync Broadcast")
        
        self._setup_matrix_tab()
        self._setup_sync_tab()
        
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
        ctk.CTkComboBox(row, values=device_names).pack(side="left", padx=5)
        
        # Volume
        ctk.CTkSlider(row, from_=0, to=100).pack(side="left", fill="x", expand=True, padx=5)
        
        # Delay
        ctk.CTkLabel(row, text="Delay:").pack(side="left", padx=5)
        delay_slider = ctk.CTkSlider(row, from_=0, to=2000)
        delay_slider.pack(side="left", padx=5)
        
        # Remove
        ctk.CTkButton(row, text="X", width=30, fg_color="red", 
                     command=lambda: row.destroy()).pack(side="right", padx=5)

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
            
            # Get selected output devices
            output_indices = []
            for widget in self.output_list_frame.winfo_children():
                # Get the first combobox in each row
                for child in widget.winfo_children():
                    if isinstance(child, ctk.CTkComboBox):
                        output_text = child.get()
                        print(f"Output text: {output_text}")
                        # Extract device name and look up its index
                        devices = self.router.get_audio_devices()
                        for dev in devices:
                            if dev['name'] in output_text:
                                output_indices.append(dev['index'])
                                print(f"Added output index: {dev['index']}")
                                break
                        break
            
            # Remove duplicates
            output_indices = list(dict.fromkeys(output_indices))
            print(f"Total unique output indices: {output_indices}")
            
            if not output_indices:
                messagebox.showerror("Error", "Please add at least one output device")
                return
            
            # Start sync with correct devices
            print(f"Starting sync: Input={input_index}, Outputs={output_indices}, UseLoopback={is_loopback}")
            try:
                self.sync_engine.start(input_index, output_indices, use_loopback=is_loopback)
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
