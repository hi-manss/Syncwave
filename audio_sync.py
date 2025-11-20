import sounddevice as sd
import pyaudiowpatch as pyaudio
import numpy as np
import threading
import time
import logging

logger = logging.getLogger(__name__)

class OutputChannel:
    def __init__(self, device_index, delay_ms=0, volume=1.0):
        self.device_index = device_index
        self.delay_ms = delay_ms
        self.volume = volume  # 0.0 to 1.0
        self.stream = None
        self.buffer = [] # Simple list buffer for now, or numpy ring buffer
        self.active = False

class SyncEngine:
    def __init__(self, network_server=None):
        self.p = pyaudio.PyAudio()
        self.input_device_index = None
        self.outputs = [] # List of OutputChannel
        self.is_running = False
        self.thread = None
        self.network_server = network_server  # Optional network server for broadcasting

    def get_devices(self):
        """Returns list of devices (both input and output)."""
        devices = []
        try:
            # Use sounddevice for better cross-platform support
            import sounddevice as sd
            device_list = sd.query_devices()
            for i, dev in enumerate(device_list):
                devices.append({
                    'index': i,
                    'name': dev['name'],
                    'max_input': dev['max_input_channels'],
                    'max_output': dev['max_output_channels'],
                    'is_loopback': 'Loopback' in dev['name'] or 'WASAPI' in dev['name']
                })
        except Exception as e:
            logger.error(f"Error listing devices: {e}")
            # Fallback to PyAudio
            for i in range(self.p.get_device_count()):
                dev = self.p.get_device_info_by_index(i)
                devices.append({
                    'index': i,
                    'name': dev['name'],
                    'max_input': dev['maxInputChannels'],
                    'max_output': dev['maxOutputChannels'],
                    'is_loopback': 'Loopback' in dev['name']
                })
        return devices

    def add_output(self, device_index):
        self.outputs.append(OutputChannel(device_index))

    def start(self, input_index, output_indices, use_loopback=False, volumes=None, delays=None):
        """Start syncing from input to multiple outputs
        
        Args:
            input_index: Input device index
            output_indices: List of output device indices
            use_loopback: Use WASAPI loopback
            volumes: List of volume levels (0-100) for each output, or None for 100%
            delays: List of delay values (ms) for each output, or None for 0ms
        """
        self.input_device_index = input_index
        self.output_indices = output_indices
        self.use_loopback = use_loopback
        
        # Store volumes and delays
        self.volumes = volumes if volumes else [100] * len(output_indices)
        self.delays = delays if delays else [0] * len(output_indices)
        
        self.is_running = True
        self.thread = threading.Thread(target=self._loop)
        self.thread.start()

    def _loop(self):
        """
        Main Audio Loop:
        1. Read chunk from Input (WASAPI Loopback or Mic).
        2. Write chunk to ALL selected Outputs.
        """
        in_stream = None
        out_streams = []
        
        try:
            # Handle WASAPI Loopback devices specially
            if self.use_loopback:
                print("🔊 Using WASAPI Loopback (Stereo Mix)")
                try:
                    # Get the default WASAPI loopback device
                    wasapi_info = self.p.get_default_wasapi_loopback()
                    dev_info = wasapi_info
                    actual_device_index = dev_info['index']
                    print(f"Found WASAPI loopback device: {dev_info['name']} (Index: {actual_device_index})")
                except Exception as e:
                    print(f"Could not get default WASAPI loopback, trying manual index: {e}")
                    dev_info = self.p.get_device_info_by_index(self.input_device_index)
                    actual_device_index = self.input_device_index
            else:
                # Regular input device
                dev_info = self.p.get_device_info_by_index(self.input_device_index)
                actual_device_index = self.input_device_index
            
            print(f"Input device info: {dev_info}")
            
            # Check if it's a loopback device (WASAPI)
            is_wasapi_loopback = dev_info.get('isLoopbackDevice', False)
            
            # For WASAPI loopback, we need to use it as an input even though it's an output device
            channels = int(dev_info.get('maxInputChannels', 2))
            if channels == 0:
                # This is likely a loopback of an output device
                channels = 2
            
            sample_rate = int(dev_info.get('defaultSampleRate', 44100))
            
            print(f"Opening input stream: Index={actual_device_index}, Channels={channels}, Rate={sample_rate}, IsLoopback={is_wasapi_loopback}")
            
            # Open input stream (pyaudiowpatch handles loopback automatically)
            # Use larger buffer to prevent distortion
            BUFFER_SIZE = 4096  # Larger buffer = smoother audio
            
            try:
                in_stream = self.p.open(
                    format=pyaudio.paInt16,
                    channels=channels,
                    rate=sample_rate,
                    input=True,
                    input_device_index=actual_device_index,
                    frames_per_buffer=BUFFER_SIZE
                )
                print(f"✓ Input stream opened with buffer size: {BUFFER_SIZE}")
            except Exception as e:
                print(f"Failed to open with rate {sample_rate}. Error: {e}")
                print("Trying with 44100 Hz...")
                # Fallback to 44100 Hz
                sample_rate = 44100
                in_stream = self.p.open(
                    format=pyaudio.paInt16,
                    channels=2,
                    rate=44100,
                    input=True,
                    input_device_index=actual_device_index,
                    frames_per_buffer=BUFFER_SIZE
                )
            
            # Open Output Streams for EACH selected device
            for output_idx in self.output_indices:
                out_dev = self.p.get_device_info_by_index(output_idx)
                print(f"Opening output stream: Index={output_idx}, Name={out_dev['name']}, Rate={sample_rate}")
                
                try:
                    stream = self.p.open(
                        format=pyaudio.paInt16,
                        channels=2,
                        rate=sample_rate,  # Match input sample rate
                        output=True,
                        output_device_index=output_idx,
                        frames_per_buffer=BUFFER_SIZE  # Same buffer size as input
                    )
                    out_streams.append(stream)
                except Exception as e:
                    print(f"⚠️ Failed to open output {out_dev['name']} at {sample_rate}Hz: {e}")
                    # Try with 44100 as fallback
                    try:
                        stream = self.p.open(
                            format=pyaudio.paInt16,
                            channels=2,
                            rate=44100,
                            output=True,
                            output_device_index=output_idx,
                            frames_per_buffer=BUFFER_SIZE
                        )
                        out_streams.append(stream)
                        print(f"✓ Opened at 44100Hz instead")
                    except:
                        print(f"❌ Could not open output device {out_dev['name']}")

            print(f"✅ Sync Engine Started: {len(out_streams)} output devices")
            
            while self.is_running:
                # Read from input (use same buffer size)
                data = in_stream.read(BUFFER_SIZE, exception_on_overflow=False)
                
                # Convert to numpy array for volume processing
                audio_array = np.frombuffer(data, dtype=np.int16)
                
                # Broadcast to ALL outputs with individual volume control
                for i, stream in enumerate(out_streams):
                    try:
                        # Apply volume (convert 0-100 to 0-1.0)
                        volume_factor = self.volumes[i] / 100.0
                        
                        if volume_factor != 1.0:
                            # Apply volume
                            adjusted_audio = (audio_array * volume_factor).astype(np.int16)
                            stream.write(adjusted_audio.tobytes())
                        else:
                            # No volume adjustment needed
                            stream.write(data)
                    except Exception as e:
                        logger.error(f"Error writing to output: {e}")
                
                # Broadcast to network clients if server is active
                if self.network_server and self.network_server.is_running:
                    self.network_server.broadcast_audio(audio_array)
                    
        except Exception as e:
            logger.error(f"Sync Engine Error: {e}")
            print(f"❌ ERROR: {e}")
            import traceback
            traceback.print_exc()
        finally:
            # Cleanup
            if in_stream:
                try:
                    in_stream.stop_stream()
                    in_stream.close()
                except:
                    pass
            for stream in out_streams:
                try:
                    stream.stop_stream()
                    stream.close()
                except:
                    pass
            print("Sync Engine Stopped")

    def stop(self):
        self.is_running = False
        if self.thread:
            self.thread.join()
