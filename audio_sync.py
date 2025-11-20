import sounddevice as sd
import pyaudiowpatch as pyaudio
import numpy as np
import threading
import time
import logging

logger = logging.getLogger(__name__)

class OutputChannel:
    def __init__(self, device_index, delay_ms=0):
        self.device_index = device_index
        self.delay_ms = delay_ms
        self.stream = None
        self.buffer = [] # Simple list buffer for now, or numpy ring buffer
        self.active = False

class SyncEngine:
    def __init__(self):
        self.p = pyaudio.PyAudio()
        self.input_device_index = None
        self.outputs = [] # List of OutputChannel
        self.is_running = False
        self.thread = None

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

    def start(self, input_index, output_indices, use_loopback=False):
        """Start syncing from input to multiple outputs"""
        self.input_device_index = input_index
        self.output_indices = output_indices
        self.use_loopback = use_loopback
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
                
                # Broadcast to ALL outputs
                for stream in out_streams:
                    try:
                        stream.write(data)
                    except Exception as e:
                        logger.error(f"Error writing to output: {e}")
                    
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
