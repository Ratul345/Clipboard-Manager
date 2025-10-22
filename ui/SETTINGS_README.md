# Settings Window Documentation

## Overview

The Settings Window provides a user-friendly interface for configuring the Clipboard Manager application. It features a tabbed interface with four main sections: General, Capture, Storage, and About.

## Features

### General Tab

**Auto-Start Configuration**
- Checkbox to enable/disable launching the application on system startup
- Platform-specific implementation:
  - Windows: Creates/removes registry entry in `HKEY_CURRENT_USER\Software\Microsoft\Windows\CurrentVersion\Run`
  - Linux: Creates/removes `.desktop` file in `~/.config/autostart/`

**Hotkey Configuration**
- Display of current global hotkey combination
- "Change" button to capture new hotkey
- Interactive key capture: Press the button, then press your desired key combination
- Validates hotkey format and updates the HotkeyHandler
- Default hotkey: `Ctrl+Shift+V`

### Capture Tab

**Content Type Toggles**
- Text: Enable/disable capturing plain text from clipboard
- Links: Enable/disable capturing URLs and web links
- Images: Enable/disable capturing images from clipboard
- Changes are applied immediately without restart
- Settings are saved to config and update the ClipboardService filters

### Storage Tab

**Storage Limit**
- Spinbox to set maximum number of clipboard items (10-10,000)
- Oldest items are automatically deleted when limit is reached
- Changes trigger storage cleanup if limit is reduced

**Data Management**
- "Clear All Data" button with confirmation dialog
- Permanently deletes all clipboard history
- Updates main window display if visible

### About Tab

**Application Information**
- Application name and version
- Description of features
- License information

## Integration

### Signals

The SettingsWindow emits the following signals:

- `settings_changed(dict)`: Emitted when any settings are saved
- `hotkey_changed(str)`: Emitted when hotkey is changed
- `capture_settings_changed(dict)`: Emitted when capture settings change
- `storage_limit_changed(int)`: Emitted when storage limit changes
- `clear_all_requested()`: Emitted when clear all data is requested

### Usage Example

```python
from models.config import Config
from ui.settings_window import SettingsWindow

# Create config and settings window
config = Config()
settings_window = SettingsWindow(config)

# Connect signals
settings_window.hotkey_changed.connect(on_hotkey_changed)
settings_window.capture_settings_changed.connect(on_capture_settings_changed)
settings_window.storage_limit_changed.connect(on_storage_limit_changed)
settings_window.clear_all_requested.connect(on_clear_all_requested)

# Show window
settings_window.show()
```

## Implementation Details

### Auto-Start Manager

The `AutoStartManager` class in `utils/autostart.py` handles platform-specific auto-start configuration:

- **Windows**: Uses `winreg` module to manage registry entries
- **Linux**: Creates `.desktop` files in the autostart directory
- Automatically detects the application path (script or executable)
- Provides methods: `enable_autostart()`, `disable_autostart()`, `is_autostart_enabled()`

### Hotkey Capture

The hotkey capture mechanism uses Qt's event filter system:

1. User clicks "Change" button
2. Input field becomes active and installs event filter
3. User presses desired key combination
4. Event filter captures modifiers (Ctrl, Shift, Alt, Super) and key
5. Constructs hotkey string (e.g., "ctrl+shift+v")
6. Validates and displays the new hotkey
7. Pressing Escape cancels the capture

### Capture Settings

The capture settings are immediately applied to the ClipboardService:

- `capture_text`: Controls whether text content is captured
- `capture_images`: Controls whether images are captured
- `capture_links`: Controls whether links are captured

The ClipboardService checks these settings before storing new clipboard items.

### Storage Settings

Storage settings affect the StorageManager:

- `max_items`: Maximum number of items to store
- When limit is reduced, `enforce_item_limit()` is called to delete oldest items
- Clear all data calls `clear_all_items()` on the StorageManager

## Testing

Run the test script to verify the settings window:

```bash
python test_settings_window.py
```

This will open the settings window and print signal emissions to the console.

## Requirements

- PyQt5
- Python 3.8+
- Platform-specific:
  - Windows: `winreg` module (built-in)
  - Linux: `.config/autostart` directory support
