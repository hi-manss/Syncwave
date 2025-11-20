# SyncWave 🎵

**Multi-device audio broadcasting with perfect synchronization**

SyncWave lets you play audio from one source (YouTube, Spotify, games, system audio) to multiple output devices simultaneously - perfect for watch parties, gaming sessions, and multi-room audio setups.

---

## ✨ Key Features

- 🎧 **Multi-Device Sync** - Broadcast to unlimited Bluetooth headphones/speakers simultaneously
- 🔧 **Auto-Calibration** - Automatically detect and compensate for Bluetooth latency
- 🎛️ **Individual Volume Control** - Each device gets its own volume slider (0-100%)
- 🌐 **Network Streaming** - Stream audio over WiFi to devices in different rooms
- ⚡ **Low Latency** - Advanced buffering for crystal-clear synchronized playback
- 🔊 **WASAPI Loopback** - Capture any system audio seamlessly

---

## 🚀 Quick Start

### Installation

```powershell
# Clone the repository
git clone https://github.com/AbhishekChauhan1112/Syncwave.git
cd Syncwave

# Create virtual environment
python -m venv venv
.\venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Launch SyncWave
python SyncWave.py
```

### Basic Usage

1. **Enable Stereo Mix** (First time only):
   - Right-click speaker icon → Sounds → Recording tab
   - Right-click empty space → Show Disabled Devices
   - Enable "Stereo Mix"

2. **Start Syncing**:
   - Launch `SyncWave.py`
   - Select **"Stereo Mix (WASAPI)"** as input
   - Click **"Add Output Device"** for each headphone/speaker
   - Click **📏 Cal** to auto-calibrate each device (optional)
   - Adjust volume sliders as needed
   - Click **"Start Sync"**
   - Play your audio (YouTube, Spotify, etc.)

---

## 🌟 Advanced Features

### Auto-Calibration
- Click the **📏 Cal** button next to any device
- System automatically detects Bluetooth latency (±5ms accuracy)
- No more manual delay adjustment!

### Network Streaming (Multi-Room Audio)

**Host Mode:**
- Go to "Network Streaming" tab
- Click "Start Server"
- Share your IP with friends

**Client Mode:**
- Go to "Network Streaming" tab
- Click "Discover Servers" to find hosts
- Connect and enjoy synchronized audio

---

## 🎯 Use Cases

- **Watch Parties** - Everyone uses their own headphones for movies
- **Gaming Sessions** - Multiple players hear game audio on individual headsets
- **Multi-Room Audio** - Stream music to different rooms over WiFi
- **Silent Parties** - DJ broadcasts to unlimited Bluetooth headphones
- **Remote Watching** - Friends join from different locations (same network)

---

## 📋 Requirements

- **OS**: Windows 10/11 (macOS/Linux support planned)
- **Python**: 3.8 or higher
- **Hardware**: Multiple audio output devices (Bluetooth headphones, speakers, etc.)
- **Network**: WiFi/Ethernet for network streaming features

---

## 🛠️ Tech Stack

- **Python** - Core application
- **PyAudioWPatch** - WASAPI loopback audio capture
- **CustomTkinter** - Modern dark-themed GUI
- **NumPy** - Efficient audio processing
- **SciPy** - Signal processing for auto-calibration
- **Zeroconf** - Network device discovery (mDNS)

---

## 🐛 Troubleshooting

### "No Input Devices Found"
**Solution:** Enable Stereo Mix in Windows Sound Settings (see Quick Start)

### Audio is Out of Sync
**Solution:** Use the Auto-Calibration feature (📏 Cal button) for each device

### Can't Discover Network Servers
**Solution:** 
- Ensure all devices are on the same WiFi network
- Check firewall allows port 5555
- Try manual IP connection

### Audio Stuttering
**Solution:**
- Close bandwidth-heavy applications
- Use Ethernet instead of WiFi for network streaming
- Reduce number of simultaneous outputs

---

## 🤝 Contributing

This is my personal project, but contributions are welcome! Feel free to:

- 🐛 Report bugs via [Issues](https://github.com/AbhishekChauhan1112/Syncwave/issues)
- 💡 Suggest features
- 🔧 Submit pull requests
- ⭐ Star the repo if you find it useful!

### Development Setup

```powershell
# Fork and clone your fork
git clone https://github.com/YOUR_USERNAME/Syncwave.git
cd Syncwave

# Create branch for your feature
git checkout -b feature/your-feature-name

# Make your changes and test
python SyncWave.py

# Commit and push
git add .
git commit -m "Add your feature"
git push origin feature/your-feature-name

# Open a Pull Request on GitHub
```

---

## 📝 Version History

- **v3.0** (2025-11-20) - Network streaming, auto-calibration, volume control
- **v2.0** - Multi-device sync with GUI
- **v1.0** - Initial release

---

## 📄 License

MIT License - see [LICENSE](LICENSE) file for details.

Free to use, modify, and distribute!

---

## 👤 Author

**Abhishek Chauhan**

- GitHub: [@AbhishekChauhan1112](https://github.com/AbhishekChauhan1112)
- Project: [Syncwave](https://github.com/AbhishekChauhan1112/Syncwave)

---

## 🙏 Acknowledgments

- Built with Python and passion for audio tech
- Thanks to the open-source community
- Special thanks to PyAudio contributors

---

**⭐ Star this repo if you find it useful!**

**🐛 Found a bug? [Open an issue](https://github.com/AbhishekChauhan1112/Syncwave/issues)**

**💬 Questions? Check [Discussions](https://github.com/AbhishekChauhan1112/Syncwave/discussions)**

---

Made with ❤️ for audiophiles everywhere
