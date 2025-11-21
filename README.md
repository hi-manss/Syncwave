# SyncWave 🎵

**Hybrid Rust+Python multi-device audio broadcasting system**

Stream system audio from one source to multiple devices simultaneously with sub-150ms latency. Perfect for watch parties, gaming sessions, and multi-room audio setups.

---

## ✨ Key Features

- 🎧 **Multi-Device Sync** - Broadcast to unlimited receivers (WiFi/LAN)
- ⚡ **High Performance** - Rust core with WASAPI Loopback (7.5x faster than pure Python)
- 🎯 **Auto Sample Rate Detection** - Automatic configuration (48kHz, 44.1kHz, etc.)
- 🌐 **UDP Broadcasting** - Low-latency streaming (~100-150ms)
- 📡 **Three Modes** - Single target, broadcast, or multi-target streaming
- 🎨 **Modern GUI** - CustomTkinter dark theme with real-time stats
- 📦 **Standalone Executable** - PyInstaller packaging for distribution

---

## 🚀 Quick Start

### For End Users

Download the standalone executable from [Releases](https://github.com/AbhishekChauhan1112/Syncwave/releases) - no installation required!

### For Developers

See the **[Developer Setup](#-developer-setup)** section below for detailed instructions including Rust installation, dependency management, and troubleshooting.

### Basic Usage

**Server (Audio Source):**
1. Launch `syncwave_app.py` or the executable
2. Go to **Server** tab
3. Choose streaming mode:
   - **Single Target**: One specific device
   - **Broadcast**: All devices on network
   - **Multi-Target**: Multiple specific devices
4. Click **"Start Server"**

**Receiver (Audio Output):**
1. Launch `syncwave_app.py` on another device
2. Go to **Receiver** tab
3. Click **"Start Receiver"**
4. Audio plays automatically with real-time latency display

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

- **Rust** (2021 edition) - High-performance audio capture core
  - `cpal` 0.15.2 - Cross-platform audio I/O
  - `PyO3` 0.20.0 - Python bindings
- **Python** 3.11+ - GUI and application logic
  - `CustomTkinter` - Modern dark-themed GUI
  - `PyAudio` / `PyAudioWPatch` - Audio output
  - `maturin` 0.20.0 - Rust-Python build system
- **Networking** - UDP broadcasting with custom protocol
- **Packaging** - PyInstaller for standalone executables

---

## 🐛 Troubleshooting

### GUI Not Responding After Starting Server
**Solution:** Rebuild Rust core with GIL release:
```bash
maturin develop --release
```

### Firewall Blocking UDP Packets
**Solution:**
```powershell
# Run as Administrator
New-NetFirewallRule -DisplayName "SyncWave" -Direction Inbound -Protocol UDP -LocalPort 5555 -Action Allow
```

### High Latency (>300ms)
**Solution:**
- Use wired Ethernet instead of WiFi
- Increase jitter buffer size (Receiver tab slider)
- Check for network congestion

### Audio Crackling/Stuttering
**Solution:**
- Increase jitter buffer from 10 to 20-50 packets
- Close bandwidth-heavy applications
- Check WiFi signal strength

### "Rust core not available" Error
**Solution:**
```bash
# Rebuild the Rust module
maturin develop --release

# Verify it's installed
python -c "import syncwave_core; print('OK')"
```

---

## 🤝 Contributing

This is my personal project, but contributions are welcome! Feel free to:

- 🐛 Report bugs via [Issues](https://github.com/AbhishekChauhan1112/Syncwave/issues)
- 💡 Suggest features
- 🔧 Submit pull requests
- ⭐ Star the repo if you find it useful!

## 🔧 Developer Setup

### Prerequisites

**1. Install Rust** (Required for audio core)
- Download from: https://rustup.rs/
- Windows: Run `rustup-init.exe` and follow prompts
- Verify: `rustc --version` and `cargo --version`
- **Restart your terminal** after installation

**2. Install Python 3.11+**
- Download from: https://www.python.org/downloads/
- ✅ Check "Add Python to PATH" during installation
- Verify: `python --version`

**3. Install Visual Studio Build Tools** (Windows only)
- Required for Rust compilation on Windows
- Download: https://visualstudio.microsoft.com/downloads/
- Install "Desktop development with C++" workload
- Or install via: `winget install Microsoft.VisualStudio.2022.BuildTools`

**4. Install CMake** (Optional - for Opus compression)
- Download from: https://cmake.org/download/
- Add to PATH during installation
- Verify: `cmake --version`

### Installation Steps

```powershell
# 1. Clone repository
git clone https://github.com/AbhishekChauhan1112/Syncwave.git
cd Syncwave

# 2. Create Python virtual environment
python -m venv venv
.\venv\Scripts\Activate.ps1

# 3. Install Python dependencies
pip install -r requirements.txt

# 4. Install Rust build tool
pip install maturin

# 5. Build Rust core
maturin develop --release

# 6. Verify installation
python -c "import syncwave_core; print('✅ Rust core loaded')"

# 7. Run the application
python syncwave_app.py
```

### Common Installation Issues

#### ❌ Issue: "error: linker `link.exe` not found"
**Cause:** Visual Studio Build Tools not installed or not in PATH  
**Solution:**
```powershell
# Install VS Build Tools
winget install Microsoft.VisualStudio.2022.BuildTools

# Or download from:
# https://visualstudio.microsoft.com/downloads/
```

#### ❌ Issue: "ModuleNotFoundError: No module named 'pyaudio'"
**Cause:** PyAudio binary unavailable for your Python version  
**Solution:**
```powershell
# Use PyAudioWPatch instead (Windows)
pip uninstall pyaudio
pip install pyaudiowpatch

# Or download PyAudio wheel from:
# https://www.lfd.uci.edu/~gohlke/pythonlibs/#pyaudio
pip install PyAudio‑0.2.11‑cp311‑cp311‑win_amd64.whl
```

#### ❌ Issue: "ImportError: DLL load failed while importing _portaudio"
**Cause:** Missing Visual C++ Redistributable  
**Solution:**
```powershell
# Install VC++ Redistributable
winget install Microsoft.VCRedist.2015+.x64

# Or download from:
# https://aka.ms/vs/17/release/vc_redist.x64.exe
```

#### ❌ Issue: "CustomTkinter" theme errors
**Cause:** Conflicting tkinter installation  
**Solution:**
```powershell
pip uninstall customtkinter
pip cache purge
pip install customtkinter --no-cache-dir
```

#### ❌ Issue: Rust compilation fails with "cannot find -lpython311"
**Cause:** Python development headers missing  
**Solution:**
```powershell
# Reinstall Python with development files
# Download installer from python.org
# ✅ Check "Install development headers/libraries"
```

#### ❌ Issue: "maturin: command not found"
**Cause:** Maturin not in PATH or venv not activated  
**Solution:**
```powershell
# Ensure venv is activated
.\venv\Scripts\Activate.ps1

# Reinstall maturin
pip install maturin --force-reinstall

# Verify
maturin --version
```

### Building Standalone Executable

```powershell
# Ensure all dependencies are installed
pip install pyinstaller

# Run automated build script
python build_app.py

# Output: dist/SyncWave.exe (~20-40 MB)
```

See **[BUILD_GUIDE.md](BUILD_GUIDE.md)** for detailed packaging instructions.

### Development Workflow

```powershell
# 1. Create feature branch
git checkout -b feature/your-feature-name

# 2. Make changes to Python code
# Edit syncwave_app.py, receiver_enhanced.py, etc.

# 3. Make changes to Rust code (if needed)
# Edit src/lib.rs
maturin develop --release  # Rebuild after Rust changes

# 4. Test your changes
python syncwave_app.py

# 5. Run tests (if available)
python -m pytest tests/

# 6. Commit and push
git add .
git commit -m "feat: Add your feature description"
git push origin feature/your-feature-name

# 7. Open Pull Request on GitHub
```

### Debugging Tips

**Enable verbose Rust logging:**
```powershell
$env:RUST_LOG="debug"
python syncwave_app.py
```

**Check Rust module location:**
```powershell
python -c "import syncwave_core; print(syncwave_core.__file__)"
```

**Test UDP networking:**
```powershell
# Terminal 1 (Server)
python -c "import socket; s=socket.socket(socket.AF_INET, socket.SOCK_DGRAM); s.bind(('0.0.0.0', 5555)); print('Listening...'); print(s.recvfrom(1024))"

# Terminal 2 (Client)
python -c "import socket; s=socket.socket(socket.AF_INET, socket.SOCK_DGRAM); s.sendto(b'test', ('127.0.0.1', 5555))"
```

### Useful Resources

- **Rust Documentation**: https://doc.rust-lang.org/book/
- **PyO3 Guide**: https://pyo3.rs/
- **cpal Audio Library**: https://docs.rs/cpal/
- **CustomTkinter Docs**: https://customtkinter.tomschimansky.com/
- **Maturin Guide**: https://www.maturin.rs/

### Project Structure

```
Syncwave/
├── src/
│   └── lib.rs              # Rust audio capture core
├── syncwave_app.py         # Main GUI application
├── receiver_enhanced.py    # Standalone receiver with jitter buffer
├── build_app.py            # PyInstaller build script
├── Cargo.toml              # Rust dependencies
├── pyproject.toml          # Python project metadata
├── requirements.txt        # Python dependencies
├── BUILD_GUIDE.md          # Detailed build instructions
├── TEST_GUIDE.md           # Testing procedures
└── README_APP.md           # End-user documentation
```

---

## 📝 Version History

- **v4.0** (2025-11-21) - Rust+Python hybrid architecture
  - 7.5x performance improvement
  - UDP broadcasting with auto sample rate detection
  - Production GUI with multi-device management
  - PyInstaller packaging
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
