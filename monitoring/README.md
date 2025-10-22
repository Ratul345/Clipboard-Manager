# Clipboard Monitoring Module

This module provides cross-platform clipboard monitoring functionality for the Clipboard Manager application.

## Architecture

The monitoring module consists of several components:

### 1. ClipboardMonitor (Base Class)
- Abstract base class for platform-specific implementations
- Provides common monitoring logic with background thread polling
- Implements callback mechanism for clipboard changes
- Handles duplicate detection using content hashing

### 2. WindowsClipboardMonitor
- Windows-specific implementation using `win32clipboard`
- Supports text (CF_UNICODETEXT, CF_TEXT) and image (CF_DIB) formats
- Implements retry logic for clipboard access (3 attempts with 100ms delay)
- Handles clipboard locking by other applications gracefully

### 3. LinuxClipboardMonitor
- Linux-specific implementation supporting both X11 and Wayland
- Auto-detects display server (X11 vs Wayland)
- Uses appropriate tools:
  - **Wayland**: `wl-paste` and `wl-copy`
  - **X11**: `xclip` or `xsel`
  - **Fallback**: `pyperclip` for basic text support
- Supports text and image clipboard content

### 4. ClipboardService
- High-level service that integrates monitoring with storage
- Handles duplicate detection to avoid storing same content twice
- Implements content type detection (text vs link vs image)
- Enforces storage limits (default: 1000 items)
- Coordinates with StorageManager and ImageStorage

## Features

### Clipboard Content Types
- **Text**: Plain text content
- **Link**: URLs and web links (auto-detected)
- **Image**: Screenshots and copied images (PNG format)

### Duplicate Detection
- Uses SHA-256 hashing for text/link content
- Prevents storing identical consecutive clipboard entries
- Efficient memory usage with hash comparison

### Storage Integration
- Automatically saves captured items to SQLite database
- Stores images as PNG files in `~/.clipboard-manager/images/`
- Enforces configurable item limits
- Cleans up old items when limit is exceeded

### Error Handling
- Retry logic for clipboard access failures
- Graceful handling of locked clipboard
- Logging of errors without crashing
- Platform-specific error handling

## Usage

### Basic Usage

```python
from storage.storage_manager import StorageManager
from storage.image_storage import ImageStorage
from monitoring.clipboard_service import ClipboardService

# Initialize components
storage_manager = StorageManager()
image_storage = ImageStorage()

# Create clipboard service
clipboard_service = ClipboardService(
    storage_manager=storage_manager,
    image_storage=image_storage,
    max_items=1000
)

# Start monitoring
clipboard_service.start()

# ... application runs ...

# Stop monitoring
clipboard_service.stop()
```

### Custom Callback

```python
from monitoring.windows_monitor import WindowsClipboardMonitor

def on_change(content, content_type):
    print(f"Clipboard changed: {content_type}")
    print(f"Content: {content[:50]}...")

monitor = WindowsClipboardMonitor()
monitor.set_callback(on_change)
monitor.start_monitoring()
```

## Platform Requirements

### Windows
- Python 3.8+
- `pywin32` package for native clipboard access
- `Pillow` for image processing

### Linux
- Python 3.8+
- `Pillow` for image processing
- `pyperclip` for fallback text support
- **X11**: `xclip` or `xsel` command-line tools
- **Wayland**: `wl-clipboard` package

Install Linux dependencies:
```bash
# Ubuntu/Debian (X11)
sudo apt-get install xclip

# Ubuntu/Debian (Wayland)
sudo apt-get install wl-clipboard

# Fedora (X11)
sudo dnf install xclip

# Fedora (Wayland)
sudo dnf install wl-clipboard
```

## Configuration

### Polling Interval
Default: 500ms (0.5 seconds)

```python
monitor = WindowsClipboardMonitor(poll_interval=0.5)
```

### Retry Settings (Windows)
```python
monitor = WindowsClipboardMonitor(
    max_retries=3,
    retry_delay=0.1  # 100ms
)
```

### Storage Limits
```python
clipboard_service = ClipboardService(
    storage_manager=storage_manager,
    image_storage=image_storage,
    max_items=1000  # Maximum items to store
)
```

## Testing

Run the integration tests:

```bash
# Basic monitoring test
python test_clipboard_monitoring.py

# Full integration test
python test_monitoring_integration.py
```

## Implementation Details

### Thread Safety
- Uses threading locks for state management
- Background thread runs as daemon
- Graceful shutdown with timeout

### Performance
- Efficient hash-based duplicate detection
- Minimal CPU usage with configurable polling interval
- Lazy image loading (only when needed)

### Memory Management
- Images stored on disk, not in memory
- Content hashing for duplicate detection
- Automatic cleanup of old items

## Troubleshooting

### Windows: "Access Denied" errors
- Some applications lock the clipboard exclusively
- Retry logic handles most cases automatically
- Check antivirus software clipboard protection

### Linux: "Command not found" errors
- Install required clipboard tools (xclip, xsel, or wl-clipboard)
- Check display server with: `echo $WAYLAND_DISPLAY` or `echo $DISPLAY`

### Images not capturing
- Ensure Pillow is installed: `pip install Pillow`
- Check image format support (PNG is most reliable)
- Some applications use proprietary clipboard formats

## Future Enhancements

- [ ] Support for rich text (RTF) format
- [ ] File path detection and handling
- [ ] Clipboard history synchronization
- [ ] Encrypted storage for sensitive content
- [ ] Custom content filters
- [ ] Clipboard change notifications
