"""ItemCard widget for displaying individual clipboard items."""

from PyQt5.QtWidgets import (
    QWidget, QHBoxLayout, QVBoxLayout, QLabel, 
    QPushButton, QSizePolicy
)
from PyQt5.QtCore import Qt, pyqtSignal, QSize
from PyQt5.QtGui import QPixmap, QFont
from datetime import datetime, timedelta
import sys
import os

# Add parent directory to path to import models
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from models.clipboard_item import ClipboardItem


class ItemCard(QWidget):
    """Widget for displaying a single clipboard item with icon, preview, and timestamp."""
    
    # Signal emitted when the delete button is clicked
    delete_clicked = pyqtSignal(ClipboardItem)
    
    # Signal emitted when the card is clicked
    card_clicked = pyqtSignal(ClipboardItem)
    
    # Signal emitted when the card is double-clicked
    card_double_clicked = pyqtSignal(ClipboardItem)
    
    def __init__(self, clipboard_item: ClipboardItem, search_query: str = ""):
        """
        Initialize an ItemCard.
        
        Args:
            clipboard_item: ClipboardItem to display
            search_query: Optional search query for highlighting matches
        """
        super().__init__()
        
        self.clipboard_item = clipboard_item
        self.search_query = search_query
        self.is_selected = False
        
        self._init_ui()
    
    def _init_ui(self):
        """Initialize the user interface components."""
        # Main layout
        main_layout = QHBoxLayout()
        main_layout.setContentsMargins(10, 8, 10, 8)
        main_layout.setSpacing(10)
        
        # Content type icon
        icon_label = QLabel()
        icon_pixmap = self._get_content_type_icon()
        if icon_pixmap and not icon_pixmap.isNull():
            icon_label.setPixmap(icon_pixmap.scaled(24, 24, Qt.KeepAspectRatio, Qt.SmoothTransformation))
        else:
            # Fallback to emoji if icon file not found
            icon_label.setText(self._get_fallback_icon())
            icon_label.setFont(QFont("Segoe UI Emoji", 20))
        icon_label.setAlignment(Qt.AlignTop | Qt.AlignLeft)
        icon_label.setFixedWidth(30)
        main_layout.addWidget(icon_label)
        
        # Content area (preview + timestamp)
        content_layout = QVBoxLayout()
        content_layout.setSpacing(4)
        
        # Preview text or image thumbnail
        if self.clipboard_item.content_type == 'image' and self.clipboard_item.image_path:
            # Show image thumbnail
            thumbnail_label = self._create_thumbnail_label()
            if thumbnail_label:
                content_layout.addWidget(thumbnail_label)
        
        # Preview text
        preview_text = self._get_preview_text()
        preview_label = QLabel(preview_text)
        preview_label.setWordWrap(True)
        preview_label.setFont(QFont("Segoe UI", 10))
        preview_label.setStyleSheet("color: #333;")
        preview_label.setTextInteractionFlags(Qt.TextSelectableByMouse)
        
        # Enable rich text if highlighting is present
        if '<span' in preview_text or '<mark>' in preview_text:
            preview_label.setTextFormat(Qt.RichText)
        
        content_layout.addWidget(preview_label)
        
        # Timestamp
        timestamp_label = QLabel(self._format_timestamp())
        timestamp_label.setFont(QFont("Segoe UI", 9))
        timestamp_label.setStyleSheet("color: #888;")
        content_layout.addWidget(timestamp_label)
        
        content_layout.addStretch()
        main_layout.addLayout(content_layout, stretch=1)
        
        # Delete button
        delete_button = QPushButton("🗑️")
        delete_button.setFixedSize(32, 32)
        delete_button.setFont(QFont("Segoe UI Emoji", 12))
        delete_button.setCursor(Qt.PointingHandCursor)
        delete_button.setStyleSheet("""
            QPushButton {
                background-color: transparent;
                border: none;
                border-radius: 6px;
            }
            QPushButton:hover {
                background-color: #FFE6E6;
            }
            QPushButton:pressed {
                background-color: #FFCCCC;
            }
        """)
        delete_button.clicked.connect(self._on_delete_clicked)
        delete_button.setToolTip("Delete this item")
        main_layout.addWidget(delete_button, alignment=Qt.AlignTop)
        
        self.setLayout(main_layout)
        
        # Set card styling
        self._update_style()
        
        # Set size policy
        self.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Minimum)
    
    def _get_content_type_icon(self) -> QPixmap:
        """
        Get icon pixmap for content type.
        
        Returns:
            QPixmap icon or None if not found
        """
        icon_files = {
            'text': 'text_icon.png',
            'link': 'link_icon.png',
            'image': 'image_icon.png'
        }
        
        icon_filename = icon_files.get(self.clipboard_item.content_type, 'text_icon.png')
        
        # Try multiple possible locations
        possible_paths = [
            os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'assets', 'icons', icon_filename),
            os.path.join(sys._MEIPASS, 'assets', 'icons', icon_filename) if getattr(sys, 'frozen', False) else None,
            os.path.join('assets', 'icons', icon_filename),
        ]
        
        for path in possible_paths:
            if path and os.path.exists(path):
                return QPixmap(path)
        
        return None
    
    def _get_fallback_icon(self) -> str:
        """
        Get fallback emoji icon for content type.
        
        Returns:
            Emoji icon string
        """
        icons = {
            'text': '📋',
            'link': '🔗',
            'image': '🖼️'
        }
        return icons.get(self.clipboard_item.content_type, '📋')
    
    def _get_preview_text(self) -> str:
        """
        Get preview text with optional highlighting.
        
        Returns:
            Preview text (possibly with HTML highlighting)
        """
        preview = self.clipboard_item.get_display_preview()
        
        # Apply highlighting if search query exists
        if self.search_query and self.search_query.strip():
            from search.search_engine import SearchEngine
            search_engine = SearchEngine()
            preview = search_engine.highlight_matches(
                preview, 
                self.search_query,
                start_tag='<span style="background-color: #ffeb3b; font-weight: bold;">',
                end_tag='</span>'
            )
            # Enable rich text for highlighting
            return preview
        
        return preview
    
    def _create_thumbnail_label(self) -> QLabel:
        """
        Create a label with image thumbnail.
        
        Returns:
            QLabel with thumbnail or None if image cannot be loaded
        """
        if not self.clipboard_item.image_path or not os.path.exists(self.clipboard_item.image_path):
            return None
        
        try:
            pixmap = QPixmap(self.clipboard_item.image_path)
            if pixmap.isNull():
                return None
            
            # Scale to thumbnail size (max 100x100, maintain aspect ratio)
            thumbnail = pixmap.scaled(
                100, 100,
                Qt.KeepAspectRatio,
                Qt.SmoothTransformation
            )
            
            thumbnail_label = QLabel()
            thumbnail_label.setPixmap(thumbnail)
            thumbnail_label.setAlignment(Qt.AlignLeft)
            
            return thumbnail_label
        except Exception:
            return None
    
    def _format_timestamp(self) -> str:
        """
        Format timestamp in relative format.
        
        Returns:
            Relative time string (e.g., "2m ago")
        """
        now = datetime.now()
        diff = now - self.clipboard_item.timestamp
        
        seconds = diff.total_seconds()
        
        if seconds < 60:
            return "just now"
        elif seconds < 3600:
            minutes = int(seconds / 60)
            return f"{minutes}m ago"
        elif seconds < 86400:
            hours = int(seconds / 3600)
            return f"{hours}h ago"
        elif seconds < 604800:  # 7 days
            days = int(seconds / 86400)
            return f"{days}d ago"
        else:
            # Show actual date for older items
            return self.clipboard_item.timestamp.strftime("%b %d, %Y")
    
    def _on_delete_clicked(self):
        """Handle delete button click."""
        self.delete_clicked.emit(self.clipboard_item)
    
    def _update_style(self):
        """Update widget styling based on selection state."""
        if self.is_selected:
            self.setStyleSheet("""
                ItemCard {
                    background-color: #E8F4FD;
                    border: 2px solid #2B7FD8;
                    border-radius: 10px;
                    padding: 8px;
                }
            """)
        else:
            self.setStyleSheet("""
                ItemCard {
                    background-color: white;
                    border: 1px solid #E5E5E5;
                    border-radius: 10px;
                    padding: 8px;
                }
                ItemCard:hover {
                    background-color: #F9F9F9;
                    border-color: #2B7FD8;
                    border-width: 1px;
                }
            """)
    
    def set_selected(self, selected: bool):
        """
        Set the selection state of this card.
        
        Args:
            selected: True if selected, False otherwise
        """
        self.is_selected = selected
        self._update_style()
    
    def mousePressEvent(self, event):
        """
        Handle mouse press event.
        
        Args:
            event: QMouseEvent
        """
        if event.button() == Qt.LeftButton:
            self.card_clicked.emit(self.clipboard_item)
        super().mousePressEvent(event)
    
    def mouseDoubleClickEvent(self, event):
        """
        Handle mouse double-click event.
        
        Args:
            event: QMouseEvent
        """
        if event.button() == Qt.LeftButton:
            self.card_double_clicked.emit(self.clipboard_item)
        super().mouseDoubleClickEvent(event)
    
    def sizeHint(self) -> QSize:
        """
        Provide size hint for the widget.
        
        Returns:
            Recommended size
        """
        return QSize(350, 80)
