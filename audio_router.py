import logging
import comtypes
from comtypes import GUID, COMMETHOD, HRESULT, IUnknown
from ctypes import wintypes
import psutil
from pycaw.pycaw import AudioUtilities

# Logger setup
logger = logging.getLogger(__name__)

# --------------------------------------------------------------------------
# COM Interface Definitions for IPolicyConfig
# --------------------------------------------------------------------------
# IPolicyConfig is an undocumented Windows interface used to set default
# audio endpoints. We'll define a minimal interface for our needs.

class IPolicyConfig(IUnknown):
    _iid_ = GUID('{f8679f50-850a-41cf-9c72-430f290290c8}')
    _methods_ = [
        # We're only implementing the SetDefaultEndpoint method
        # The vtable index might vary by Windows version
        # This is a simplified approach - we'll skip methods we don't need
        # by using placeholder stubs if needed.
        
        # Note: Since IPolicyConfig is undocumented and varies by Windows version,
        # and we're having issues with complex type definitions,
        # we'll use a different approach: just use the SetDefaultEndpoint via index
        
        # For now, we'll leave this minimal and focus on using pycaw's existing
        # capabilities for getting audio sessions.
    ]

# Alternative: We won't use IPolicyConfig directly for per-app routing
# Instead, we'll guide users to use Windows' built-in "App volume and device preferences"
# or use Virtual Cables for the Sync Engine approach.

# --------------------------------------------------------------------------
# AppRouter Class
# --------------------------------------------------------------------------

class AppRouter:
    def __init__(self):
        self.policy_config = None
        self._init_policy_config()

    def _init_policy_config(self):
        """
        Initialize PolicyConfig (Currently disabled).
        Per-app routing requires undocumented Windows APIs that are version-specific.
        For now, users can manually set app devices in Windows Settings > System > Sound.
        """
        self.policy_config = None
        # Commenting out due to complexity and Windows version compatibility issues
        # try:
        #     clsid = GUID('{870af99c-171d-4f9e-af0d-e63df40c2bc9}') 
        #     self.policy_config = comtypes.CoCreateInstance(
        #         clsid, 
        #         IPolicyConfig, 
        #         comtypes.CLSCTX_ALL
        # )
        # except Exception as e:
        #     logger.error(f"Failed to initialize IPolicyConfig: {e}")

    def get_audio_devices(self):
        """Returns a list of output devices using PyAudio (for consistent indices)."""
        import pyaudiowpatch as pyaudio
        devices = []
        try:
            p = pyaudio.PyAudio()
            for i in range(p.get_device_count()):
                dev = p.get_device_info_by_index(i)
                if dev['maxOutputChannels'] > 0:  # Output device
                    devices.append({
                        'index': i,
                        'name': dev['name'],
                        'channels': dev['maxOutputChannels']
                    })
            p.terminate()
        except Exception as e:
            logger.error(f"Error listing devices: {e}")
        return devices

    def get_active_apps(self):
        """Returns a list of processes currently having an audio session."""
        apps = []
        try:
            sessions = AudioUtilities.GetAllSessions()
            for session in sessions:
                if session.Process:
                    apps.append({
                        'pid': session.ProcessId,
                        'name': session.Process.name(),
                        'session': session
                    })
        except Exception as e:
            logger.error(f"Error listing apps: {e}")
        return apps

    def set_app_device(self, pid, device_id):
        """
        Sets the output device for a specific process.
        
        NOTE: True per-app routing via public API is not supported by Windows.
        The 'App volume and device preferences' menu uses private APIs.
        
        We will attempt to use the IPolicyConfig::SetPersistedDefaultAudioEndpoint
        if we can find the correct vtable index.
        
        For now, we might have to fallback to a simpler 'Router' model:
        The USER selects 'Spotify' in our app.
        Our app finds the Spotify Window/Process.
        
        Actually, since we are building a 'Sync Engine' too, 
        the most reliable way to 'Route' Spotify to Headphone 1 is:
        1. User sets Spotify Output to 'Virtual Cable A' (Manual or via App if possible).
        2. Our App reads 'Virtual Cable A'.
        3. Our App plays to 'Headphone 1'.
        
        This method `set_app_device` will try to automate Step 1.
        """
        # This is a placeholder for the complex COM logic.
        # If we can't automate Step 1 reliably, we will instruct the user.
        pass

if __name__ == "__main__":
    router = AppRouter()
    print("Active Audio Apps:", [app['name'] for app in router.get_active_apps()])
