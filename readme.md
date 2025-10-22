<div align="center">
  <img src="assets/icons/clipboard.png" alt="Clipboard Manager Logo" width="200"/>
  
  # Clipboard Manager

  **A lightweight clipboard manager that saves your copy history and lets you reuse it anytime.**
  
  Never lose what you copied again!

  [![Version](https://img.shields.io/badge/Version-1.1.0-brightgreen.svg)](https://github.com/Ratul345/Clipboard-Manager/releases)
  [![License: MIT](https://img.shields.io/badge/License-MIT-blue.svg)](https://opensource.org/licenses/MIT)
  [![Platform](https://img.shields.io/badge/Platform-Windows%20%7C%20Linux-lightgrey)](https://github.com/Ratul345/Clipboard-Manager)
  [![Python](https://img.shields.io/badge/Python-3.8%2B-blue)](https://www.python.org/)
  
</div>

---

## Features

- 📋 **Automatic Clipboard Monitoring** - Captures everything you copy (text, links, images)
- 🔍 **Fast Search** - Quickly find items with real-time search filtering
- 🖼️ **Image Support** - Stores and displays copied images
- 🔗 **Smart Link Detection** - Automatically identifies and highlights URLs
- 🎨 **Clean UI** - Modern, intuitive interface with item cards
- 🔔 **System Tray Integration** - Runs quietly in the background
- ⌨️ **Keyboard Navigation** - Arrow keys, Enter, Delete, and Escape shortcuts
- 🗑️ **Easy Management** - Delete individual items or clear all history
- 💾 **Persistent Storage** - SQLite database keeps your history across sessions
- 🖥️ **Cross-Platform** - Works on Windows and Linux (X11/Wayland)

## Requirements

- Python 3.8 or higher
- Windows or major Linux distributions (Ubuntu, Fedora, Debian)
- For Linux: X11 or Wayland display server

## Installation

### Option 1: Pre-built Binaries

#### Windows (Recommended)

1. Download `ClipboardManager.exe` from the [Releases](https://github.com/Ratul345/Clipboard-Manager/releases) page
2. Run the executable - no installation required!
3. (Optional) Create a shortcut and place it in your Startup folder for auto-start

#### Linux

**Pre-built binaries for Linux are not yet available.** Please use Option 2 (From Source) below.

> **Note:** Linux users can run the application from source code. Pre-built Linux binaries may be added in future releases if there's demand.

### Option 2: From Source

#### 1. Clone the repository

```bash
git clone https://github.com/Ratul345/Clipboard-Manager.git
cd Clipboard-Manager
```

#### 2. Create and activate virtual environment

**Windows:**
```cmd
python -m venv myenv
myenv\Scripts\activate
```

**Linux:**
```bash
python3 -m venv myenv
source myenv/bin/activate
```

#### 3. Install dependencies

```bash
pip install -r requirements.txt
```

**Note:** Platform-specific dependencies are automatically installed:
- **Windows:** `pywin32`, `keyboard`
- **Linux:** `pynput`

#### 4. Run from source

```bash
python app.py
```

## Usage

### First Launch

1. **Windows:** Double-click `ClipboardManager.exe` or run `python app.py` from source
2. **Linux:** Run `clipboard-manager` or `python app.py` from source
3. Look for the clipboard icon in your system tray:
   - **Windows:** Bottom-right corner (notification area)
   - **Linux:** Top-right corner (system tray)

### Quick Start Guide

1. **Copy something** - Copy any text, link, or image as you normally would (Ctrl+C)
2. **Open the manager** - Click the system tray icon or press **Ctrl+Shift+V**
3. **Find your item** - Use the search bar or scroll through your history
4. **Reuse it** - Click an item or press Enter to copy it back to your clipboard
5. **Paste** - Use Ctrl+V to paste the selected item anywhere

### Keyboard Shortcuts

| Shortcut | Action |
|----------|--------|
| **Ctrl+Shift+V** | Open/close Clipboard Manager window |
| **↑ / ↓** | Navigate through clipboard items |
| **Enter** | Copy selected item to clipboard and close window |
| **Delete** | Remove selected item from history |
| **Escape** | Close window (app continues running in background) |
| **Ctrl+F** | Focus search bar |

### System Tray Menu

Right-click the system tray icon to access:

- **Open Clipboard Manager** - Show/hide the main window
- **Settings** - Configure preferences (hotkey, auto-start, storage limits)
- **Exit** - Quit the application completely

### Main Window Features

**Search Bar**
- Type to filter items in real-time
- Searches through text content and URLs
- Case-insensitive matching
- Clear search to show all items

**Item Cards**
- 📋 **Text** - Regular text content
- 🔗 **Link** - URLs and web links
- 🖼️ **Image** - Screenshots and copied images
- Shows preview and timestamp (e.g., "2m ago")
- Click to select and copy to clipboard

**Actions**
- **Click item** - Copy to clipboard and close window
- **Double-click** - Quick copy and close
- **Trash icon** - Delete individual item
- **Clear All button** - Remove all history (with confirmation)

## Development

### Project Structure

```
Clipboard Manager/
├── app.py                      # Main application entry point
├── models/
│   ├── clipboard_item.py       # ClipboardItem data model
│   └── config.py               # Configuration management
├── storage/
│   ├── storage_manager.py      # SQLite database operations
│   └── image_storage.py        # Image file storage
├── monitoring/
│   ├── clipboard_service.py    # Clipboard monitoring service
│   ├── windows_monitor.py      # Windows-specific monitor
│   └── linux_monitor.py        # Linux-specific monitor
├── search/
│   └── search_engine.py        # Search and filtering logic
├── ui/
│   ├── main_window.py          # Main GUI window
│   ├── item_card.py            # Individual item display widget
│   └── system_tray.py          # System tray integration
├── utils/
│   └── platform_utils.py       # Cross-platform utilities
├── data/
│   ├── clipboard.db            # SQLite database (auto-created)
│   └── images/                 # Stored images (auto-created)
└── logs/
    └── clipboard_manager.log   # Application logs (auto-created)
```

### Dependencies

- **PyQt5** - GUI framework
- **pystray** - System tray integration
- **Pillow** - Image processing
- **pyperclip** - Clipboard access
- **pywin32** (Windows) - Advanced clipboard monitoring
- **keyboard** (Windows) - Global hotkey support
- **pynput** (Linux) - Global hotkey support

### Running Tests

```bash
# Run all tests
python -m pytest

# Run specific test file
python -m pytest tests/test_storage.py

# Run with coverage
python -m pytest --cov=. --cov-report=html
```

## Screenshots

> **Note:** Screenshots will be added in a future update. The application features:
> - Clean, modern interface with search bar at the top
> - Scrollable list of clipboard items with icons and previews
> - System tray integration with context menu
> - Settings window with tabbed interface

## Configuration

Configuration is stored in `~/.clipboard-manager/config.json` (auto-created on first run):

```json
{
  "max_items": 1000,
  "auto_start": false,
  "hotkey": "ctrl+shift+v",
  "capture_text": true,
  "capture_images": true,
  "capture_links": true,
  "theme": "light"
}
```

You can edit this file manually or use the Settings window in the application.

### Data Storage Locations

- **Windows:**
  - Config: `%USERPROFILE%\.clipboard-manager\config.json`
  - Database: `%USERPROFILE%\.clipboard-manager\clipboard.db`
  - Images: `%USERPROFILE%\.clipboard-manager\images\`
  - Logs: `%USERPROFILE%\.clipboard-manager\app.log`

- **Linux:**
  - Config: `~/.clipboard-manager/config.json`
  - Database: `~/.clipboard-manager/clipboard.db`
  - Images: `~/.clipboard-manager/images/`
  - Logs: `~/.clipboard-manager/app.log`

## Settings

Access settings by right-clicking the system tray icon and selecting "Settings".

### General Settings

- **Launch on Startup** - Automatically start when your computer boots
- **Global Hotkey** - Customize the keyboard shortcut (default: Ctrl+Shift+V)
- **Theme** - Choose between light and dark mode

### Capture Settings

Toggle what types of content to capture:
- **Text** - Regular text content
- **Images** - Screenshots and copied images
- **Links** - URLs and web addresses

### Storage Settings

- **Max Items** - Limit clipboard history (default: 1000 items)
- **Clear All Data** - Remove all stored clipboard items and images

## Troubleshooting

### Windows

**Issue:** Application won't start
- **Solution:** Make sure you have .NET Framework 4.5+ installed
- **Solution:** Try running as administrator (right-click → Run as administrator)
- **Solution:** Check Windows Defender or antivirus isn't blocking the app

**Issue:** Clipboard monitoring not working
- **Solution:** Ensure `pywin32` is installed if running from source: `pip install pywin32`
- **Solution:** Close other clipboard managers that might conflict
- **Solution:** Restart the application

**Issue:** System tray icon not showing
- **Solution:** Check Windows notification area settings (Settings → Personalization → Taskbar)
- **Solution:** Look in the hidden icons area (click the ^ arrow in system tray)
- **Solution:** Enable "Always show all icons in the notification area"

**Issue:** Hotkey (Ctrl+Shift+V) not working
- **Solution:** Check if another application is using the same hotkey
- **Solution:** Try changing the hotkey in Settings
- **Solution:** Run the application as administrator

**Issue:** Images not being captured
- **Solution:** Make sure "Images" is enabled in Settings → Capture Settings
- **Solution:** Check that the `data/images/` directory is writable
- **Solution:** Try copying the image again

### Linux

**Issue:** Application won't start
- **Solution:** Make the executable file executable: `chmod +x clipboard-manager`
- **Solution:** Install missing dependencies: `sudo apt-get install libx11-6 libxcb1`
- **Solution:** Check error logs: `~/.clipboard-manager/app.log`

**Issue:** Clipboard monitoring not working
- **Solution:** Ensure you're running X11 or Wayland (check with `echo $XDG_SESSION_TYPE`)
- **Solution:** For X11, install xclip: `sudo apt-get install xclip`
- **Solution:** For Wayland, install wl-clipboard: `sudo apt-get install wl-clipboard`
- **Solution:** Restart your display server or reboot

**Issue:** System tray icon not showing
- **Solution:** Install a system tray extension for your desktop environment
  - **GNOME:** Install "AppIndicator Support" extension
  - **KDE:** System tray should work by default
  - **XFCE:** Check panel settings for system tray plugin
- **Solution:** Try running from terminal to see error messages

**Issue:** Permission errors
- **Solution:** Ensure `~/.clipboard-manager/` directory is writable
- **Solution:** Check file permissions: `ls -la ~/.clipboard-manager/`
- **Solution:** Fix permissions: `chmod -R u+rw ~/.clipboard-manager/`

**Issue:** Hotkey not working
- **Solution:** Check if your desktop environment supports global hotkeys
- **Solution:** Try a different hotkey combination in Settings
- **Solution:** For Wayland, global hotkeys may have limited support

### General Issues

**Issue:** Application uses too much memory
- **Solution:** Reduce "Max Items" in Settings → Storage Settings
- **Solution:** Clear old items: Settings → Storage Settings → Clear All Data
- **Solution:** Disable image capture if you don't need it

**Issue:** Database errors or corruption
- **Solution:** Backup and delete `~/.clipboard-manager/clipboard.db`
- **Solution:** Restart the application (it will create a new database)

**Issue:** Search not finding items
- **Solution:** Search is case-insensitive and matches substrings
- **Solution:** Try shorter search terms
- **Solution:** Clear search and scroll manually

**Issue:** Items not persisting after restart
- **Solution:** Check that the database file exists: `~/.clipboard-manager/clipboard.db`
- **Solution:** Ensure the application has write permissions
- **Solution:** Check logs for database errors

### Getting Help

If you encounter issues not listed here:

1. Check the log file:
   - **Windows:** `%USERPROFILE%\.clipboard-manager\app.log`
   - **Linux:** `~/.clipboard-manager/app.log`

2. Search existing [GitHub Issues](https://github.com/Ratul345/Clipboard-Manager/issues)

3. Create a new issue with:
   - Your operating system and version
   - Steps to reproduce the problem
   - Relevant log entries
   - Screenshots if applicable

## License

MIT License

## Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

### Development Setup

1. Fork the repository
2. Create a feature branch: `git checkout -b feature-name`
3. Make your changes
4. Run tests: `python -m pytest`
5. Commit: `git commit -am 'Add feature'`
6. Push: `git push origin feature-name`
7. Submit a Pull Request

## Building from Source

See [build_scripts/README.md](build_scripts/README.md) for detailed build instructions.

### Quick Build

**Windows:**
```cmd
pip install pyinstaller
build_scripts\build_windows.bat
```

**Linux:**
```bash
pip install pyinstaller
chmod +x build_scripts/build_linux.sh
./build_scripts/build_linux.sh
```

## Frequently Asked Questions

**Q: Is my clipboard data sent to the cloud?**
A: No. All data is stored locally on your computer in `~/.clipboard-manager/`. Nothing is sent to any server.

**Q: Can I sync my clipboard history across devices?**
A: Not currently. This is a planned feature for a future release.

**Q: How much disk space does it use?**
A: It depends on your usage. Text items are very small (bytes), but images can be larger. The default limit is 1000 items.

**Q: Can I exclude certain applications from being monitored?**
A: Not yet, but this is a planned feature. For now, you can pause monitoring by exiting the app temporarily.

**Q: Does it work with password managers?**
A: Yes, but be cautious. Passwords copied to clipboard will be stored in history. Consider using the "Clear All" feature regularly or pausing the app when copying sensitive data.

**Q: Can I change the hotkey?**
A: Yes! Go to Settings → General → Global Hotkey and set your preferred combination.

**Q: Why isn't my clipboard history showing after restart?**
A: Check that the database file exists and is readable. See the Troubleshooting section for database issues.

**Q: Can I export my clipboard history?**
A: Not currently, but this is planned for a future release.

## Roadmap

- [x] Basic clipboard monitoring
- [x] Text and link support
- [x] Image support
- [x] Search functionality
- [x] System tray integration
- [x] Global hotkey (Ctrl+Shift+V)
- [x] Settings window
- [x] Auto-start on system boot
- [x] Persistent storage
- [x] Cross-platform support (Windows & Linux)
- [ ] Custom themes (dark mode)
- [ ] Pin favorite items
- [ ] Categories and tags
- [ ] Export/import history
- [ ] Exclude specific applications
- [ ] Rich text formatting
- [ ] Cloud sync (optional)
- [ ] Mobile companion app

## Credits

Inspired by clipboard managers like Ditto, Clipper, and CopyQ.
