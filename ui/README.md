# UI Module - Clipboard Manager

This module contains the graphical user interface components for the Clipboard Manager application.

## Components

### MainWindow (`main_window.py`)

The main application window that displays clipboard history and provides search functionality.

**Features:**
- 400x600 pixel window with always-on-top behavior
- Search bar with real-time filtering
- Scrollable list of clipboard items
- "Clear All" button with confirmation dialog
- Keyboard navigation (Arrow keys, Enter, Delete, Esc)
- Automatic window centering on display
- Show/hide toggle functionality

**Key Methods:**
- `load_items()` - Load clipboard items from storage
- `add_new_item(item)` - Add a new item to the display (for dynamic updates)
- `toggle_visibility()` - Show or hide the window
- `_on_search_changed(text)` - Handle real-time search filtering
- `_select_current_item()` - Copy selected item to clipboard and close window
- `_delete_current_item()` - Delete the selected item

**Signals:**
- `item_selected` - Emitted when an item is selected for copying
- `item_deleted` - Emitted when an item is deleted
- `all_items_cleared` - Emitted when all items are cleared

### ItemCard (`item_card.py`)

A custom widget for displaying individual clipboard items with rich formatting.

**Features:**
- Content type icons (📋 text, 🔗 link, 🖼️ image)
- Preview text with truncation
- Relative timestamps (e.g., "2m ago", "5h ago")
- Image thumbnails (100x100 max, maintains aspect ratio)
- Delete button on each card
- Visual selection highlighting
- Search term highlighting in preview text

**Key Methods:**
- `set_selected(selected)` - Update visual selection state
- `_get_preview_text()` - Get preview with optional search highlighting
- `_create_thumbnail_label()` - Create image thumbnail display
- `_format_timestamp()` - Format timestamp in relative format

**Signals:**
- `delete_clicked` - Emitted when delete button is clicked
- `card_clicked` - Emitted when card is clicked
- `card_double_clicked` - Emitted when card is double-clicked

## Usage Example

```python
from PyQt5.QtWidgets import QApplication
from storage.storage_manager import StorageManager
from search.search_engine import SearchEngine
from ui.main_window import MainWindow

# Create Qt application
app = QApplication([])

# Initialize components
storage_manager = StorageManager()
search_engine = SearchEngine()

# Create main window
main_window = MainWindow(storage_manager, search_engine)

# Show window
main_window.show()

# Run application
app.exec_()
```

## Keyboard Shortcuts

- **Arrow Keys** - Navigate through items
- **Enter** - Select highlighted item and copy to clipboard
- **Delete** - Remove selected item
- **Esc** - Close window

## Styling

The UI uses custom stylesheets for a modern, clean appearance:
- Rounded corners on input fields and buttons
- Hover effects on interactive elements
- Visual feedback for selection
- Color-coded buttons (red for destructive actions)

## Integration with Other Modules

- **Storage Manager** - Loads and saves clipboard items
- **Search Engine** - Filters items based on search query
- **Clipboard Item Model** - Represents individual clipboard entries

## Testing

Run the test script to verify GUI functionality:

```bash
python test_gui.py
```

This will create sample data and display the main window for manual testing.
