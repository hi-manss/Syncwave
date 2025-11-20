"""
Auto-Calibration Engine for SyncWave
Automatically detects and compensates for Bluetooth/device latency
"""

import numpy as np
import pyaudiowpatch as pyaudio
import time
import logging
from scipy import signal
from scipy.fft import fft, ifft

logger = logging.getLogger(__name__)

class CalibrationEngine:
    def __init__(self):
        self.p = pyaudio.PyAudio()
        self.sample_rate = 44100
        self.calibration_tone_freq = 1000  # 1kHz beep
        self.tone_duration = 0.5  # 500ms beep
        self.is_calibrating = False
        
    def generate_calibration_tone(self, duration=0.5, frequency=1000):
        """Generate a calibration beep tone"""
        samples = int(self.sample_rate * duration)
        t = np.linspace(0, duration, samples, False)
        
        # Generate sine wave
        tone = np.sin(2 * np.pi * frequency * t)
        
        # Apply envelope to avoid clicks (fade in/out)
        envelope = np.ones_like(tone)
        fade_samples = int(0.01 * self.sample_rate)  # 10ms fade
        envelope[:fade_samples] = np.linspace(0, 1, fade_samples)
        envelope[-fade_samples:] = np.linspace(1, 0, fade_samples)
        
        tone = tone * envelope * 0.5  # Scale to 50% volume
        
        # Convert to int16 for playback
        tone_int16 = (tone * 32767).astype(np.int16)
        
        return tone_int16
    
    def play_tone(self, tone_data, device_index):
        """Play calibration tone through specified device"""
        try:
            stream = self.p.open(
                format=pyaudio.paInt16,
                channels=1,
                rate=self.sample_rate,
                output=True,
                output_device_index=device_index,
                frames_per_buffer=1024
            )
            
            # Add silence before and after for clean detection
            silence = np.zeros(int(0.2 * self.sample_rate), dtype=np.int16)
            full_signal = np.concatenate([silence, tone_data, silence])
            
            stream.write(full_signal.tobytes())
            stream.stop_stream()
            stream.close()
            
            return True
        except Exception as e:
            logger.error(f"Error playing tone: {e}")
            return False
    
    def record_audio(self, duration, device_index, use_loopback=False):
        """Record audio for calibration"""
        try:
            if use_loopback:
                # Use WASAPI loopback
                try:
                    wasapi_info = self.p.get_default_wasapi_loopback()
                    device_index = wasapi_info['index']
                except:
                    pass
            
            stream = self.p.open(
                format=pyaudio.paInt16,
                channels=1,
                rate=self.sample_rate,
                input=True,
                input_device_index=device_index,
                frames_per_buffer=1024
            )
            
            frames = []
            num_chunks = int(self.sample_rate * duration / 1024)
            
            for _ in range(num_chunks):
                data = stream.read(1024, exception_on_overflow=False)
                frames.append(data)
            
            stream.stop_stream()
            stream.close()
            
            # Convert to numpy array
            audio_data = b''.join(frames)
            audio_array = np.frombuffer(audio_data, dtype=np.int16)
            
            return audio_array
        except Exception as e:
            logger.error(f"Error recording audio: {e}")
            return None
    
    def detect_delay_cross_correlation(self, reference_signal, recorded_signal):
        """
        Detect delay between two signals using cross-correlation
        Returns delay in milliseconds
        """
        try:
            # Normalize signals
            reference = reference_signal.astype(np.float64)
            recorded = recorded_signal.astype(np.float64)
            
            reference = reference / np.max(np.abs(reference))
            recorded = recorded / np.max(np.abs(recorded))
            
            # Compute cross-correlation
            correlation = signal.correlate(recorded, reference, mode='full')
            
            # Find peak (maximum correlation)
            lags = signal.correlation_lags(len(recorded), len(reference), mode='full')
            lag = lags[np.argmax(correlation)]
            
            # Convert samples to milliseconds
            delay_ms = (lag / self.sample_rate) * 1000
            
            # Get correlation strength (0-1)
            correlation_strength = np.max(correlation) / (len(reference) * len(recorded))
            
            return delay_ms, correlation_strength
        except Exception as e:
            logger.error(f"Error in cross-correlation: {e}")
            return None, 0
    
    def calibrate_device(self, output_device_index, input_device_index=None, use_loopback=True, callback=None):
        """
        Calibrate a single output device
        
        Args:
            output_device_index: Device to play tone through
            input_device_index: Device to record from (or None for loopback)
            use_loopback: Use WASAPI loopback for recording
            callback: Optional callback function for progress updates
            
        Returns:
            delay_ms: Detected delay in milliseconds
            confidence: Confidence score (0-1)
        """
        self.is_calibrating = True
        
        try:
            if callback:
                callback("Generating calibration tone...")
            
            # Generate tone
            tone = self.generate_calibration_tone(
                duration=self.tone_duration,
                frequency=self.calibration_tone_freq
            )
            
            if callback:
                callback("Playing tone and recording...")
            
            # Start recording first (to catch the tone from the beginning)
            record_duration = self.tone_duration + 1.0  # Extra buffer
            
            # Start recording in a separate thread
            import threading
            recorded_audio = None
            
            def record_thread():
                nonlocal recorded_audio
                if use_loopback:
                    recorded_audio = self.record_audio(record_duration, 0, use_loopback=True)
                else:
                    recorded_audio = self.record_audio(record_duration, input_device_index)
            
            record_t = threading.Thread(target=record_thread)
            record_t.start()
            
            # Small delay to ensure recording started
            time.sleep(0.1)
            
            # Play tone
            self.play_tone(tone, output_device_index)
            
            # Wait for recording to complete
            record_t.join()
            
            if recorded_audio is None:
                if callback:
                    callback("ERROR: Recording failed")
                return None, 0
            
            if callback:
                callback("Analyzing delay...")
            
            # Detect delay using cross-correlation
            delay_ms, confidence = self.detect_delay_cross_correlation(tone, recorded_audio)
            
            if delay_ms is not None:
                # Ensure delay is positive and reasonable
                if delay_ms < 0:
                    delay_ms = 0
                elif delay_ms > 5000:  # More than 5 seconds is unrealistic
                    delay_ms = 0
                    confidence = 0
                
                if callback:
                    callback(f"Calibration complete! Detected delay: {delay_ms:.1f}ms (confidence: {confidence:.2f})")
                
                return delay_ms, confidence
            else:
                if callback:
                    callback("ERROR: Could not detect delay")
                return None, 0
                
        except Exception as e:
            logger.error(f"Calibration error: {e}")
            if callback:
                callback(f"ERROR: {e}")
            return None, 0
        finally:
            self.is_calibrating = False
    
    def calibrate_multiple_devices(self, output_devices, input_device_index=None, use_loopback=True, callback=None):
        """
        Calibrate multiple output devices
        
        Returns:
            dict: {device_index: (delay_ms, confidence)}
        """
        results = {}
        
        for i, device_idx in enumerate(output_devices):
            if callback:
                callback(f"Calibrating device {i+1}/{len(output_devices)}...")
            
            delay, confidence = self.calibrate_device(
                device_idx,
                input_device_index,
                use_loopback,
                callback
            )
            
            results[device_idx] = (delay, confidence)
            
            # Small delay between calibrations
            time.sleep(0.5)
        
        return results
    
    def test_sync_quality(self, output_devices, delays_ms, input_device_index=None, use_loopback=True):
        """
        Test sync quality by playing tones with configured delays
        Returns sync accuracy metric
        """
        # TODO: Implement sync quality test
        # Play tones on all devices simultaneously with their delays
        # Record and analyze if they align properly
        pass
    
    def cleanup(self):
        """Cleanup resources"""
        try:
            self.p.terminate()
        except:
            pass


# Example usage
if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    
    calibrator = CalibrationEngine()
    
    # List devices
    p = pyaudio.PyAudio()
    print("\n=== Available Output Devices ===")
    for i in range(p.get_device_count()):
        dev = p.get_device_info_by_index(i)
        if dev['maxOutputChannels'] > 0:
            print(f"[{i}] {dev['name']}")
    p.terminate()
    
    # Example: Calibrate device
    output_device = int(input("\nEnter output device index to calibrate: "))
    
    def progress_callback(message):
        print(f"[CALIBRATION] {message}")
    
    delay, confidence = calibrator.calibrate_device(
        output_device,
        use_loopback=True,
        callback=progress_callback
    )
    
    if delay is not None:
        print(f"\n✅ Calibration successful!")
        print(f"   Detected delay: {delay:.1f} ms")
        print(f"   Confidence: {confidence:.2%}")
    else:
        print(f"\n❌ Calibration failed")
    
    calibrator.cleanup()
