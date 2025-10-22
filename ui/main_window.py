"""Main GUI window for Clipboard Manager."""

from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QLineEdit, QListWidget, 
    QPushButton, QMessageBox, QScrollArea, QListWidgetItem
)
from PyQt5.QtCore import Qt, pyqtSignal, QSize
from PyQt5.QtGui import QIcon
import sys
import os

# Add parent directory to path to import modules
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from storage.storage_manager import StorageManager
from search.search_engine import SearchEngine
from models.clipboard_item import ClipboardItem
from ui.item_card import ItemCard


class MainWindow(QWidget):
    """Main window for displaying and managing clipboard history."""
    
    # Signal emitted when an item is selected for copying
    item_selected = pyqtSignal(ClipboardItem)
    
    # Signal emitted when an item is deleted
    item_deleted = pyqtSignal(int)
    
    # Signal emitted when all items are cleared
    all_items_cleared = pyqtSignal()
    
    # Signal emitted when window visibility changes
    visibility_changed = pyqtSignal(bool)
    
    def __init__(self, storage_manager: StorageManager, search_engine: SearchEngine):
        """
        Initialize the main window.
        
        Args:
            storage_manager: StorageManager instance for data access
            search_engine: SearchEngine instance for filtering items
        """
        super().__init__()
        
        self.storage_manager = storage_manager
        self.search_engine = search_engine
        self.clipboard_items = []
        self.filtered_items = []
        self.selected_index = -1
        
        # Animation support (optional)
        self.fade_animation = None
        
        self._init_ui()
    
    def _init_ui(self):
        """Initialize the user interface components."""
        # Window properties
        self.setWindowTitle("Clipboard Manager")
        self.setFixedSize(400, 600)
        
        # Set window icon
        icon_path = self._get_icon_path()
        if os.path.exists(icon_path):
            self.setWindowIcon(QIcon(icon_path))
        
        # Set window to always-on-top
        self.setWindowFlags(
            Qt.Window | 
            Qt.WindowStaysOnTopHint
        )
        
        # Main layout
        layout = QVBoxLayout()
        layout.setContentsMargins(10, 10, 10, 10)
        layout.setSpacing(10)
        
        # Search bar
        self.search_input = QLineEdit()
        self.search_input.setPlaceholderText("🔍 Search clipboard history...")
        self.search_input.textChanged.connect(self._on_search_changed)
        self.search_input.setStyleSheet("""
            QLineEdit {
                padding: 8px;
                font-size: 14px;
                border: 2px solid #ccc;
                border-radius: 5px;
            }
            QLineEdit:focus {
                border-color: #4CAF50;
            }
        """)
        layout.addWidget(self.search_input)
        
        # Scrollable list widget for clipboard items
        self.item_list = QListWidget()
        self.item_list.setStyleSheet("""
            QListWidget {
                border: 1px solid #ddd;
                border-radius: 5px;
                background-color: #fafafa;
            }
            QListWidget::item {
                padding: 10px;
                border-bottom: 1px solid #eee;
            }
            QListWidget::item:selected {
                background-color: #e3f2fd;
                color: #000;
            }
            QListWidget::item:hover {
                background-color: #f5f5f5;
            }
        """)
        self.item_list.setVerticalScrollMode(QListWidget.ScrollPerPixel)
        self.item_list.itemClicked.connect(self._on_item_clicked)
        self.item_list.itemDoubleClicked.connect(self._on_item_double_clicked)
        layout.addWidget(self.item_list)
        
        # Clear All button
        self.clear_all_button = QPushButton("Clear All")
        self.clear_all_button.clicked.connect(self._on_clear_all_clicked)
        self.clear_all_button.setStyleSheet("""
            QPushButton {
                padding: 10px;
                font-size: 14px;
                background-color: #f44336;
                color: white;
                border: none;
                border-radius: 5px;
            }
            QPushButton:hover {
                background-color: #d32f2f;
            }
            QPushButton:pressed {
                background-color: #b71c1c;
            }
        """)
        layout.addWidget(self.clear_all_button)
        
        self.setLayout(layout)
    
    def _on_search_changed(self, text: str):
        """
        Handle search input changes.
        
        Args:
            text: Current search text
        """
        if text.strip():
            # Filter items using search engine
            self.filtered_items = self.search_engine.search(text, self.clipboard_items)
        else:
            # Show all items when search is empty
            self.filtered_items = self.clipboard_items.copy()
        
        self._refresh_item_list()
    
    def _on_item_clicked(self, item):
        """
        Handle single click on an item.
        
        Args:
            item: QListWidgetItem that was clicked
        """
        # Update selected index
        self.selected_index = self.item_list.currentRow()
        self._update_item_selection()
    
    def _on_item_card_clicked(self, clipboard_item: ClipboardItem):
        """
        Handle click on an ItemCard.
        
        Args:
            clipboard_item: ClipboardItem that was clicked
        """
        # Find the index of this item
        for i, item in enumerate(self.filtered_items):
            if item.id == clipboard_item.id:
                self.selected_index = i
                self.item_list.setCurrentRow(i)
                self._update_item_selection()
                break
    
    def _on_item_card_double_clicked(self, clipboard_item: ClipboardItem):
        """
        Handle double-click on an ItemCard (quick selection).
        
        Args:
            clipboard_item: ClipboardItem that was double-clicked
        """
        # Find and select this item
        for i, item in enumerate(self.filtered_items):
            if item.id == clipboard_item.id:
                self.selected_index = i
                self._select_current_item()
                break
    
    def _on_item_card_delete(self, clipboard_item: ClipboardItem):
        """
        Handle delete button click on an ItemCard.
        
        Args:
            clipboard_item: ClipboardItem to delete
        """
        # Delete from storage
        if self.storage_manager.delete_item(clipboard_item.id):
            # Remove from local lists
            self.clipboard_items = [item for item in self.clipboard_items if item.id != clipboard_item.id]
            self.filtered_items = [item for item in self.filtered_items if item.id != clipboard_item.id]
            
            # Refresh display
            self._refresh_item_list()
            
            # Emit signal
            self.item_deleted.emit(clipboard_item.id)
            
            # Adjust selected index
            if self.selected_index >= len(self.filtered_items):
                self.selected_index = len(self.filtered_items) - 1
            
            # Update selection
            if self.selected_index >= 0:
                self.item_list.setCurrentRow(self.selected_index)
                self._update_item_selection()
    
    def _update_item_selection(self):
        """Update visual selection state of all item cards."""
        for i in range(self.item_list.count()):
            list_item = self.item_list.item(i)
            item_card = self.item_list.itemWidget(list_item)
            if item_card:
                item_card.set_selected(i == self.selected_index)
    
    def _on_item_double_clicked(self, item):
        """
        Handle double click on an item (quick selection).
        
        Args:
            item: QListWidgetItem that was double-clicked
        """
        self._select_current_item()
    
    def _on_clear_all_clicked(self):
        """Handle Clear All button click with confirmation."""
        # Show confirmation dialog
        reply = QMessageBox.question(
            self,
            'Clear All Items',
            'Are you sure you want to delete all clipboard items? This cannot be undone.',
            QMessageBox.Yes | QMessageBox.No,
            QMessageBox.No
        )
        
        if reply == QMessageBox.Yes:
            # Clear all items from storage
            if self.storage_manager.clear_all_items():
                self.clipboard_items.clear()
                self.filtered_items.clear()
                self._refresh_item_list()
                self.all_items_cleared.emit()
    
    def _select_current_item(self):
        """Select the currently highlighted item and copy to clipboard."""
        if self.selected_index >= 0 and self.selected_index < len(self.filtered_items):
            selected_item = self.filtered_items[self.selected_index]
            
            # Copy to clipboard
            if selected_item.copy_to_clipboard():
                # Move item to top of history (most recent)
                self._move_item_to_top(selected_item)
                
                # Emit signal
                self.item_selected.emit(selected_item)
                
                # Close window after selection
                self.hide()
    
    def _move_item_to_top(self, item: ClipboardItem):
        """
        Move an item to the top of the history after reuse.
        
        Args:
            item: ClipboardItem to move to top
        """
        # Remove from current position in clipboard_items
        self.clipboard_items = [i for i in self.clipboard_items if i.id != item.id]
        
        # Add to beginning
        self.clipboard_items.insert(0, item)
        
        # Update timestamp to current time
        from datetime import datetime
        item.timestamp = datetime.now()
        
        # Update in storage (save with new timestamp)
        # Note: This would require an update method in StorageManager
        # For now, we just update the in-memory list
    
    def _delete_current_item(self):
        """Delete the currently selected item."""
        if self.selected_index >= 0 and self.selected_index < len(self.filtered_items):
            selected_item = self.filtered_items[self.selected_index]
            
            # Delete from storage
            if self.storage_manager.delete_item(selected_item.id):
                # Remove from local lists
                self.clipboard_items = [item for item in self.clipboard_items if item.id != selected_item.id]
                self.filtered_items = [item for item in self.filtered_items if item.id != selected_item.id]
                
                # Refresh display
                self._refresh_item_list()
                
                # Emit signal
                self.item_deleted.emit(selected_item.id)
                
                # Adjust selected index
                if self.selected_index >= len(self.filtered_items):
                    self.selected_index = len(self.filtered_items) - 1
                
                # Update selection
                if self.selected_index >= 0:
                    self.item_list.setCurrentRow(self.selected_index)
    
    def _refresh_item_list(self):
        """Refresh the item list display."""
        self.item_list.clear()
        
        # Get current search query for highlighting
        search_query = self.search_input.text()
        
        for item in self.filtered_items:
            # Create ItemCard widget
            item_card = ItemCard(item, search_query)
            item_card.delete_clicked.connect(self._on_item_card_delete)
            item_card.card_clicked.connect(self._on_item_card_clicked)
            item_card.card_double_clicked.connect(self._on_item_card_double_clicked)
            
            # Create list item
            list_item = QListWidgetItem(self.item_list)
            list_item.setSizeHint(item_card.sizeHint())
            
            # Add to list
            self.item_list.addItem(list_item)
            self.item_list.setItemWidget(list_item, item_card)
    

    
    def load_items(self):
        """Load clipboard items from storage."""
        self.clipboard_items = self.storage_manager.get_all_items()
        self.filtered_items = self.clipboard_items.copy()
        self._refresh_item_list()
    
    def add_new_item(self, item: ClipboardItem):
        """
        Add a new clipboard item to the display.
        
        Args:
            item: ClipboardItem to add
        """
        # Add to beginning of list (newest first)
        self.clipboard_items.insert(0, item)
        
        # Update filtered items if no search is active
        if not self.search_input.text().strip():
            self.filtered_items = self.clipboard_items.copy()
        else:
            # Re-apply search filter
            self.filtered_items = self.search_engine.search(
                self.search_input.text(), 
                self.clipboard_items
            )
        
        self._refresh_item_list()
    
    def keyPressEvent(self, event):
        """
        Handle keyboard events.
        
        Args:
            event: QKeyEvent
        """
        key = event.key()
        
        # Arrow key navigation
        if key == Qt.Key_Up:
            if self.selected_index > 0:
                self.selected_index -= 1
                self.item_list.setCurrentRow(self.selected_index)
                self._update_item_selection()
        elif key == Qt.Key_Down:
            if self.selected_index < len(self.filtered_items) - 1:
                self.selected_index += 1
                self.item_list.setCurrentRow(self.selected_index)
                self._update_item_selection()
        
        # Enter key to select
        elif key == Qt.Key_Return or key == Qt.Key_Enter:
            self._select_current_item()
        
        # Delete key to remove item
        elif key == Qt.Key_Delete:
            self._delete_current_item()
        
        # Escape key to close window
        elif key == Qt.Key_Escape:
            self.hide()
        
        else:
            # Pass other events to parent
            super().keyPressEvent(event)
    
    def showEvent(self, event):
        """
        Handle window show event.
        
        Args:
            event: QShowEvent
        """
        # Load items when window is shown
        self.load_items()
        
        # Clear search
        self.search_input.clear()
        
        # Focus search input
        self.search_input.setFocus()
        
        # Reset selection
        self.selected_index = -1
        
        # Position window at center of screen
        self._center_on_screen()
        
        # Emit visibility changed signal
        self.visibility_changed.emit(True)
        
        super().showEvent(event)
    
    def _get_icon_path(self):
        """Get the path to the icon file."""
        # Try multiple possible locations
        possible_paths = [
            os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'assets', 'icons', 'clipboard.png'),
            os.path.join(sys._MEIPASS, 'assets', 'icons', 'clipboard.png') if getattr(sys, 'frozen', False) else None,
            'assets/icons/clipboard.png',
        ]
        
        for path in possible_paths:
            if path and os.path.exists(path):
                return path
        
        # Return default path
        return possible_paths[0]
    
    def _center_on_screen(self):
        """Position window at the center of the active screen."""
        from PyQt5.QtWidgets import QApplication
        
        # Get screen geometry
        screen = QApplication.primaryScreen()
        screen_geometry = screen.geometry()
        
        # Calculate center position
        x = (screen_geometry.width() - self.width()) // 2
        y = (screen_geometry.height() - self.height()) // 2
        
        self.move(x, y)
    
    def toggle_visibility(self):
        """Toggle window visibility (show/hide)."""
        if self.isVisible():
            self.hide()
        else:
            self.show()
    
    def hideEvent(self, event):
        """
        Handle window hide event.
        
        Args:
            event: QHideEvent
        """
        # Emit visibility changed signal
        self.visibility_changed.emit(False)
        
        # Optional: Add fade-out animation here if desired
        super().hideEvent(event)
    
    def focusOutEvent(self, event):
        """
        Handle focus out event.
        
        Args:
            event: QFocusEvent
        """
        # Optional: Could auto-hide when focus is lost
        # For now, just pass to parent
        super().focusOutEvent(event)
