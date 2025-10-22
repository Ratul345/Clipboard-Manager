"""System tray integration for Clipboard Manager."""

import sys
import os
from PyQt5.QtWidgets import QSystemTrayIcon, QMenu, QAction
from PyQt5.QtGui import QIcon, QPixmap, QPainter, QColor
from PyQt5.QtCore import QObject, pyqtSignal


class SystemTray(QObject):
    """System tray icon and menu for Clipboard Manager."""
    
    # Signals
    open_requested = pyqtSignal()
    settings_requested = pyqtSignal()
    exit_requested = pyqtSignal()
    
    def __init__(self, parent=None):
        """
        Initialize the system tray icon.
        
        Args:
            parent: Parent QObject (optional)
        """
        super().__init__(parent)
        
        self.tray_icon = None
        self.menu = None
        self.is_window_open = False
        
        self._create_icon()
        self._create_menu()
        self._setup_tray()
    
    def _create_icon(self):
        """Load clipboard icon from assets folder."""
        # Get the icon path
        icon_path = self._get_icon_path()
        
        if os.path.exists(icon_path):
            # Load icon from file
            self.normal_icon = QIcon(icon_path)
            
            # Create highlighted version by tinting the icon
            pixmap = QPixmap(icon_path)
            pixmap_highlighted = QPixmap(pixmap.size())
            pixmap_highlighted.fill(QColor(0, 0, 0, 0))
            
            painter = QPainter(pixmap_highlighted)
            painter.setRenderHint(QPainter.Antialiasing)
            
            # Draw original icon
            painter.drawPixmap(0, 0, pixmap)
            
            # Apply green tint overlay for highlighted state
            painter.setCompositionMode(QPainter.CompositionMode_SourceAtop)
            painter.fillRect(pixmap_highlighted.rect(), QColor(76, 175, 80, 100))
            
            painter.end()
            
            self.highlighted_icon = QIcon(pixmap_highlighted)
        else:
            # Fallback: Create simple icons programmatically if file not found
            self._create_fallback_icon()
    
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
        
        # Return default path even if it doesn't exist (will trigger fallback)
        return possible_paths[0]
    
    def _create_fallback_icon(self):
        """Create a simple clipboard icon as fallback."""
        # Create a 64x64 pixmap for the icon
        pixmap = QPixmap(64, 64)
        pixmap.fill(QColor(0, 0, 0, 0))  # Transparent background
        
        painter = QPainter(pixmap)
        painter.setRenderHint(QPainter.Antialiasing)
        
        # Draw clipboard shape
        painter.setBrush(QColor(255, 255, 255))
        painter.setPen(QColor(0, 0, 0, 200))
        painter.drawRoundedRect(12, 16, 40, 44, 4, 4)
        
        # Clip at top
        painter.setBrush(QColor(100, 100, 100))
        painter.drawRoundedRect(24, 12, 16, 8, 2, 2)
        
        # Lines representing text
        painter.setPen(QColor(100, 100, 100, 180))
        painter.drawLine(18, 28, 46, 28)
        painter.drawLine(18, 36, 46, 36)
        painter.drawLine(18, 44, 40, 44)
        
        painter.end()
        
        self.normal_icon = QIcon(pixmap)
        
        # Create highlighted version
        pixmap_highlighted = QPixmap(64, 64)
        pixmap_highlighted.fill(QColor(0, 0, 0, 0))
        
        painter = QPainter(pixmap_highlighted)
        painter.setRenderHint(QPainter.Antialiasing)
        
        painter.setBrush(QColor(76, 175, 80))
        painter.setPen(QColor(0, 0, 0, 200))
        painter.drawRoundedRect(12, 16, 40, 44, 4, 4)
        
        painter.setBrush(QColor(56, 142, 60))
        painter.drawRoundedRect(24, 12, 16, 8, 2, 2)
        
        painter.setPen(QColor(255, 255, 255, 220))
        painter.drawLine(18, 28, 46, 28)
        painter.drawLine(18, 36, 46, 36)
        painter.drawLine(18, 44, 40, 44)
        
        painter.end()
        
        self.highlighted_icon = QIcon(pixmap_highlighted)
    
    def _create_menu(self):
        """Create the context menu for the system tray."""
        self.menu = QMenu()
        
        # Open action
        self.open_action = QAction("Open Clipboard Manager", self)
        self.open_action.triggered.connect(self._on_open_clicked)
        self.menu.addAction(self.open_action)
        
        self.menu.addSeparator()
        
        # Settings action
        self.settings_action = QAction("Settings", self)
        self.settings_action.triggered.connect(self._on_settings_clicked)
        self.menu.addAction(self.settings_action)
        
        self.menu.addSeparator()
        
        # Exit action
        self.exit_action = QAction("Exit", self)
        self.exit_action.triggered.connect(self._on_exit_clicked)
        self.menu.addAction(self.exit_action)
    
    def _setup_tray(self):
        """Set up the system tray icon."""
        self.tray_icon = QSystemTrayIcon(self)
        self.tray_icon.setIcon(self.normal_icon)
        self.tray_icon.setToolTip("Clipboard Manager")
        self.tray_icon.setContextMenu(self.menu)
        
        # Connect activation signal (single click on icon)
        self.tray_icon.activated.connect(self._on_tray_activated)
    
    def _on_tray_activated(self, reason):
        """
        Handle tray icon activation.
        
        Args:
            reason: QSystemTrayIcon.ActivationReason
        """
        # On left click or double click, open the main window
        if reason in (QSystemTrayIcon.Trigger, QSystemTrayIcon.DoubleClick):
            self.open_requested.emit()
    
    def _on_open_clicked(self):
        """Handle Open menu item click."""
        self.open_requested.emit()
    
    def _on_settings_clicked(self):
        """Handle Settings menu item click."""
        self.settings_requested.emit()
    
    def _on_exit_clicked(self):
        """Handle Exit menu item click."""
        self.exit_requested.emit()
    
    def show(self):
        """Show the system tray icon."""
        if self.tray_icon:
            self.tray_icon.show()
    
    def hide(self):
        """Hide the system tray icon."""
        if self.tray_icon:
            self.tray_icon.hide()
    
    def set_window_state(self, is_open: bool):
        """
        Update tray icon state based on window visibility.
        
        Args:
            is_open: True if main window is open, False otherwise
        """
        self.is_window_open = is_open
        
        if self.tray_icon:
            if is_open:
                self.tray_icon.setIcon(self.highlighted_icon)
            else:
                self.tray_icon.setIcon(self.normal_icon)
    
    def show_message(self, title: str, message: str, icon=QSystemTrayIcon.Information, duration=3000):
        """
        Show a notification message from the system tray.
        
        Args:
            title: Notification title
            message: Notification message
            icon: QSystemTrayIcon icon type
            duration: Duration in milliseconds
        """
        if self.tray_icon and self.tray_icon.isVisible():
            self.tray_icon.showMessage(title, message, icon, duration)
