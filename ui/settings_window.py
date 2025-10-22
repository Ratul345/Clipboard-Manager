"""Settings window for Clipboard Manager configuration."""

import sys
import os
from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QTabWidget, QLabel,
    QCheckBox, QPushButton, QLineEdit, QSpinBox, QMessageBox,
    QGroupBox, QFormLayout, QScrollArea
)
from PyQt5.QtCore import Qt, pyqtSignal
from PyQt5.QtGui import QFont

# Add parent directory to path to import modules
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from models.config import Config
from utils.autostart import AutoStartManager
from version import __version__, APP_NAME


class SettingsWindow(QWidget):
    """Settings window with tabbed interface for configuration."""
    
    # Signals
    settings_changed = pyqtSignal(dict)  # Emitted when settings are saved
    hotkey_changed = pyqtSignal(str)  # Emitted when hotkey is changed
    capture_settings_changed = pyqtSignal(dict)  # Emitted when capture settings change
    storage_limit_changed = pyqtSignal(int)  # Emitted when storage limit changes
    clear_all_requested = pyqtSignal()  # Emitted when clear all data is requested
    
    def __init__(self, config: Config, parent=None):
        """
        Initialize settings window.
        
        Args:
            config: Config instance for managing settings
            parent: Parent widget (optional)
        """
        super().__init__(parent)
        
        self.config = config
        self.autostart_manager = AutoStartManager()
        self._init_ui()
        self._load_settings()
    
    def _init_ui(self):
        """Initialize the user interface."""
        # Window properties
        self.setWindowTitle("Settings")
        self.setFixedSize(600, 550)
        
        # Frameless window with rounded corners
        self.setWindowFlags(
            Qt.Window | 
            Qt.WindowStaysOnTopHint |
            Qt.FramelessWindowHint
        )
        self.setAttribute(Qt.WA_TranslucentBackground)
        
        # Main container
        main_container = QWidget()
        main_container.setObjectName("mainContainer")
        main_container.setStyleSheet("""
            #mainContainer {
                background-color: #F3F3F3;
                border-radius: 12px;
                border: 1px solid rgba(0, 0, 0, 0.1);
            }
        """)
        
        # Main layout
        layout = QVBoxLayout()
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)
        
        # Title bar
        title_bar = self._create_title_bar()
        layout.addWidget(title_bar)
        
        # Content area
        content_widget = QWidget()
        content_layout = QVBoxLayout()
        content_layout.setContentsMargins(20, 15, 20, 20)
        content_layout.setSpacing(15)
        
        # Tab widget with modern style
        self.tab_widget = QTabWidget()
        self.tab_widget.setStyleSheet("""
            QTabWidget::pane {
                border: none;
                background-color: white;
                border-radius: 8px;
                padding: 15px;
            }
            QTabBar::tab {
                background-color: transparent;
                color: #666666;
                padding: 10px 30px;
                margin-right: 5px;
                border: none;
                border-top-left-radius: 6px;
                border-top-right-radius: 6px;
                font-family: 'Segoe UI', sans-serif;
                font-size: 13px;
                min-width: 80px;
            }
            QTabBar::tab:selected {
                background-color: white;
                color: #2B7FD8;
                font-weight: 600;
            }
            QTabBar::tab:hover:!selected {
                background-color: rgba(255, 255, 255, 0.5);
            }
        """)
        
        # Create tabs
        self.general_tab = self._create_general_tab()
        self.capture_tab = self._create_capture_tab()
        self.storage_tab = self._create_storage_tab()
        self.about_tab = self._create_about_tab()
        
        # Add tabs
        self.tab_widget.addTab(self.general_tab, "General")
        self.tab_widget.addTab(self.capture_tab, "Capture")
        self.tab_widget.addTab(self.storage_tab, "Storage")
        self.tab_widget.addTab(self.about_tab, "About")
        
        content_layout.addWidget(self.tab_widget)
        
        # Button layout
        button_layout = QHBoxLayout()
        button_layout.setSpacing(10)
        button_layout.addStretch()
        
        # Cancel button
        self.cancel_button = QPushButton("Cancel")
        self.cancel_button.clicked.connect(self.close)
        self.cancel_button.setFixedHeight(40)
        self.cancel_button.setCursor(Qt.PointingHandCursor)
        self.cancel_button.setStyleSheet("""
            QPushButton {
                padding: 10px 25px;
                background-color: white;
                color: #666666;
                border: 1px solid #E0E0E0;
                border-radius: 8px;
                font-size: 13px;
                font-family: 'Segoe UI', sans-serif;
                font-weight: 600;
            }
            QPushButton:hover {
                background-color: #F5F5F5;
                border-color: #CCCCCC;
            }
            QPushButton:pressed {
                background-color: #EEEEEE;
            }
        """)
        button_layout.addWidget(self.cancel_button)
        
        # Save button
        self.save_button = QPushButton("Save Changes")
        self.save_button.clicked.connect(self._on_save_clicked)
        self.save_button.setFixedHeight(40)
        self.save_button.setCursor(Qt.PointingHandCursor)
        self.save_button.setStyleSheet("""
            QPushButton {
                padding: 10px 25px;
                background-color: #2B7FD8;
                color: white;
                border: none;
                border-radius: 8px;
                font-size: 13px;
                font-family: 'Segoe UI', sans-serif;
                font-weight: 600;
            }
            QPushButton:hover {
                background-color: #2470C7;
            }
            QPushButton:pressed {
                background-color: #1E5FB8;
            }
        """)
        button_layout.addWidget(self.save_button)
        
        content_layout.addLayout(button_layout)
        
        content_widget.setLayout(content_layout)
        layout.addWidget(content_widget)
        
        main_container.setLayout(layout)
        
        # Set main container
        container_layout = QVBoxLayout()
        container_layout.setContentsMargins(0, 0, 0, 0)
        container_layout.addWidget(main_container)
        self.setLayout(container_layout)
        
        # Enable mouse tracking for dragging
        self.mouse_pressed = False
        self.mouse_pos = None
    
    def _create_title_bar(self):
        """Create custom title bar."""
        from PyQt5.QtGui import QPixmap
        
        title_bar = QWidget()
        title_bar.setFixedHeight(45)
        title_bar.setStyleSheet("""
            QWidget {
                background-color: #2B7FD8;
                border-top-left-radius: 12px;
                border-top-right-radius: 12px;
            }
        """)
        
        title_layout = QHBoxLayout()
        title_layout.setContentsMargins(15, 0, 10, 0)
        title_layout.setSpacing(10)
        
        # Settings icon
        icon_label = QLabel("⚙️")
        icon_label.setStyleSheet("""
            QLabel {
                font-size: 18px;
                background: transparent;
            }
        """)
        title_layout.addWidget(icon_label)
        
        # Title
        title_label = QLabel("Settings")
        title_label.setStyleSheet("""
            QLabel {
                color: white;
                font-size: 14px;
                font-family: 'Segoe UI', sans-serif;
                font-weight: 600;
                background: transparent;
            }
        """)
        title_layout.addWidget(title_label)
        
        title_layout.addStretch()
        
        # Close button
        close_button = QPushButton("✕")
        close_button.setFixedSize(40, 30)
        close_button.setCursor(Qt.PointingHandCursor)
        close_button.clicked.connect(self.close)
        close_button.setStyleSheet("""
            QPushButton {
                background-color: transparent;
                color: white;
                border: none;
                border-radius: 4px;
                font-size: 16px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: rgba(255, 255, 255, 0.1);
            }
            QPushButton:pressed {
                background-color: rgba(255, 255, 255, 0.2);
            }
        """)
        title_layout.addWidget(close_button)
        
        title_bar.setLayout(title_layout)
        
        # Make draggable
        title_bar.mousePressEvent = self._title_bar_mouse_press
        title_bar.mouseMoveEvent = self._title_bar_mouse_move
        title_bar.mouseReleaseEvent = self._title_bar_mouse_release
        
        return title_bar
    
    def _title_bar_mouse_press(self, event):
        """Handle mouse press on title bar."""
        if event.button() == Qt.LeftButton:
            self.mouse_pressed = True
            self.mouse_pos = event.globalPos() - self.frameGeometry().topLeft()
    
    def _title_bar_mouse_move(self, event):
        """Handle mouse move on title bar."""
        if self.mouse_pressed:
            self.move(event.globalPos() - self.mouse_pos)
    
    def _title_bar_mouse_release(self, event):
        """Handle mouse release on title bar."""
        self.mouse_pressed = False
    
    def _create_general_tab(self) -> QWidget:
        """Create the General settings tab."""
        tab = QWidget()
        tab.setStyleSheet("background-color: transparent;")
        layout = QVBoxLayout()
        layout.setContentsMargins(0, 10, 0, 0)
        layout.setSpacing(20)
        
        # Auto-start group
        autostart_group = QGroupBox("Startup")
        autostart_group.setStyleSheet("""
            QGroupBox {
                font-family: 'Segoe UI', sans-serif;
                font-size: 14px;
                font-weight: 600;
                color: #1F1F1F;
                border: none;
                margin-top: 10px;
            }
            QGroupBox::title {
                subcontrol-origin: margin;
                left: 0px;
                padding: 0 5px 0 0;
            }
        """)
        autostart_layout = QVBoxLayout()
        autostart_layout.setContentsMargins(0, 15, 0, 0)
        
        self.autostart_checkbox = QCheckBox("Launch on system startup")
        self.autostart_checkbox.setStyleSheet("""
            QCheckBox {
                font-family: 'Segoe UI', sans-serif;
                font-size: 13px;
                color: #333333;
                spacing: 8px;
            }
            QCheckBox::indicator {
                width: 18px;
                height: 18px;
                border-radius: 4px;
                border: 2px solid #CCCCCC;
                background-color: white;
            }
            QCheckBox::indicator:hover {
                border-color: #2B7FD8;
            }
            QCheckBox::indicator:checked {
                background-color: #2B7FD8;
                border-color: #2B7FD8;
                image: url(none);
            }
        """)
        autostart_layout.addWidget(self.autostart_checkbox)
        
        autostart_group.setLayout(autostart_layout)
        layout.addWidget(autostart_group)
        
        # Hotkey group
        hotkey_group = QGroupBox("Global Hotkey")
        hotkey_group.setStyleSheet("""
            QGroupBox {
                font-family: 'Segoe UI', sans-serif;
                font-size: 14px;
                font-weight: 600;
                color: #1F1F1F;
                border: none;
                margin-top: 10px;
            }
            QGroupBox::title {
                subcontrol-origin: margin;
                left: 0px;
                padding: 0 5px 0 0;
            }
        """)
        hotkey_layout = QVBoxLayout()
        hotkey_layout.setContentsMargins(0, 15, 0, 0)
        hotkey_layout.setSpacing(10)
        
        hotkey_input_layout = QHBoxLayout()
        hotkey_input_layout.setSpacing(10)
        
        self.hotkey_input = QLineEdit()
        self.hotkey_input.setPlaceholderText("e.g., ctrl+shift+v")
        self.hotkey_input.setReadOnly(True)
        self.hotkey_input.setFixedHeight(36)
        self.hotkey_input.setStyleSheet("""
            QLineEdit {
                padding: 8px 12px;
                font-size: 13px;
                font-family: 'Segoe UI', sans-serif;
                background-color: #F9F9F9;
                border: 1px solid #E0E0E0;
                border-radius: 6px;
                color: #1F1F1F;
            }
            QLineEdit:focus {
                border: 2px solid #2B7FD8;
                background-color: white;
            }
        """)
        hotkey_input_layout.addWidget(self.hotkey_input)
        
        self.capture_hotkey_button = QPushButton("Change")
        self.capture_hotkey_button.clicked.connect(self._on_capture_hotkey_clicked)
        self.capture_hotkey_button.setFixedHeight(36)
        self.capture_hotkey_button.setCursor(Qt.PointingHandCursor)
        self.capture_hotkey_button.setStyleSheet("""
            QPushButton {
                padding: 8px 20px;
                background-color: white;
                color: #2B7FD8;
                border: 1px solid #2B7FD8;
                border-radius: 6px;
                font-size: 13px;
                font-family: 'Segoe UI', sans-serif;
                font-weight: 600;
            }
            QPushButton:hover {
                background-color: #E8F4FD;
            }
            QPushButton:pressed {
                background-color: #D0E8FA;
            }
            QPushButton:disabled {
                background-color: #F5F5F5;
                color: #CCCCCC;
                border-color: #E0E0E0;
            }
        """)
        hotkey_input_layout.addWidget(self.capture_hotkey_button)
        
        hotkey_layout.addLayout(hotkey_input_layout)
        
        hotkey_help = QLabel("Press the button and then press your desired key combination")
        hotkey_help.setStyleSheet("""
            QLabel {
                color: #888888;
                font-size: 11px;
                font-family: 'Segoe UI', sans-serif;
            }
        """)
        hotkey_layout.addWidget(hotkey_help)
        
        hotkey_group.setLayout(hotkey_layout)
        layout.addWidget(hotkey_group)
        
        layout.addStretch()
        tab.setLayout(layout)
        return tab
    
    def _create_capture_tab(self) -> QWidget:
        """Create the Capture settings tab."""
        tab = QWidget()
        tab.setStyleSheet("background-color: transparent;")
        layout = QVBoxLayout()
        layout.setContentsMargins(0, 10, 0, 0)
        layout.setSpacing(20)
        
        # Content types group
        content_group = QGroupBox("Content Types to Capture")
        content_group.setStyleSheet("""
            QGroupBox {
                font-family: 'Segoe UI', sans-serif;
                font-size: 14px;
                font-weight: 600;
                color: #1F1F1F;
                border: none;
                margin-top: 10px;
            }
            QGroupBox::title {
                subcontrol-origin: margin;
                left: 0px;
                padding: 0 5px 0 0;
            }
        """)
        content_layout = QVBoxLayout()
        content_layout.setContentsMargins(0, 15, 0, 0)
        content_layout.setSpacing(12)
        
        checkbox_style = """
            QCheckBox {
                font-family: 'Segoe UI', sans-serif;
                font-size: 13px;
                color: #333333;
                spacing: 8px;
            }
            QCheckBox::indicator {
                width: 18px;
                height: 18px;
                border-radius: 4px;
                border: 2px solid #CCCCCC;
                background-color: white;
            }
            QCheckBox::indicator:hover {
                border-color: #2B7FD8;
            }
            QCheckBox::indicator:checked {
                background-color: #2B7FD8;
                border-color: #2B7FD8;
            }
        """
        
        self.capture_text_checkbox = QCheckBox("Text")
        self.capture_text_checkbox.setToolTip("Capture plain text from clipboard")
        self.capture_text_checkbox.setStyleSheet(checkbox_style)
        content_layout.addWidget(self.capture_text_checkbox)
        
        self.capture_links_checkbox = QCheckBox("Links")
        self.capture_links_checkbox.setToolTip("Capture URLs and web links")
        self.capture_links_checkbox.setStyleSheet(checkbox_style)
        content_layout.addWidget(self.capture_links_checkbox)
        
        self.capture_images_checkbox = QCheckBox("Images")
        self.capture_images_checkbox.setToolTip("Capture images from clipboard")
        self.capture_images_checkbox.setStyleSheet(checkbox_style)
        content_layout.addWidget(self.capture_images_checkbox)
        
        content_group.setLayout(content_layout)
        layout.addWidget(content_group)
        
        # Info label
        info_label = QLabel("Changes will be applied immediately")
        info_label.setStyleSheet("""
            QLabel {
                color: #888888;
                font-size: 11px;
                font-family: 'Segoe UI', sans-serif;
                padding: 10px;
                background-color: #F9F9F9;
                border-radius: 6px;
            }
        """)
        layout.addWidget(info_label)
        
        layout.addStretch()
        tab.setLayout(layout)
        return tab
    
    def _create_storage_tab(self) -> QWidget:
        """Create the Storage settings tab."""
        tab = QWidget()
        tab.setStyleSheet("background-color: transparent;")
        layout = QVBoxLayout()
        layout.setContentsMargins(0, 10, 0, 0)
        layout.setSpacing(20)
        
        # Storage limit group
        limit_group = QGroupBox("Storage Limit")
        limit_group.setStyleSheet("""
            QGroupBox {
                font-family: 'Segoe UI', sans-serif;
                font-size: 14px;
                font-weight: 600;
                color: #1F1F1F;
                border: none;
                margin-top: 10px;
            }
            QGroupBox::title {
                subcontrol-origin: margin;
                left: 0px;
                padding: 0 5px 0 0;
            }
        """)
        limit_layout = QVBoxLayout()
        limit_layout.setContentsMargins(0, 15, 0, 0)
        limit_layout.setSpacing(10)
        
        limit_label = QLabel("Maximum items:")
        limit_label.setStyleSheet("""
            QLabel {
                font-family: 'Segoe UI', sans-serif;
                font-size: 13px;
                color: #333333;
            }
        """)
        limit_layout.addWidget(limit_label)
        
        self.max_items_spinbox = QSpinBox()
        self.max_items_spinbox.setMinimum(10)
        self.max_items_spinbox.setMaximum(10000)
        self.max_items_spinbox.setSingleStep(100)
        self.max_items_spinbox.setSuffix(" items")
        self.max_items_spinbox.setFixedHeight(36)
        self.max_items_spinbox.setStyleSheet("""
            QSpinBox {
                padding: 8px 12px;
                font-size: 13px;
                font-family: 'Segoe UI', sans-serif;
                background-color: white;
                border: 1px solid #E0E0E0;
                border-radius: 6px;
                color: #1F1F1F;
            }
            QSpinBox:focus {
                border: 2px solid #2B7FD8;
            }
            QSpinBox::up-button, QSpinBox::down-button {
                width: 20px;
                border-radius: 3px;
            }
            QSpinBox::up-button:hover, QSpinBox::down-button:hover {
                background-color: #E8F4FD;
            }
        """)
        limit_layout.addWidget(self.max_items_spinbox)
        
        limit_help = QLabel("Oldest items will be automatically deleted when limit is reached")
        limit_help.setStyleSheet("""
            QLabel {
                color: #888888;
                font-size: 11px;
                font-family: 'Segoe UI', sans-serif;
            }
        """)
        limit_layout.addWidget(limit_help)
        
        limit_group.setLayout(limit_layout)
        layout.addWidget(limit_group)
        
        # Data management group
        data_group = QGroupBox("Data Management")
        data_group.setStyleSheet("""
            QGroupBox {
                font-family: 'Segoe UI', sans-serif;
                font-size: 14px;
                font-weight: 600;
                color: #1F1F1F;
                border: none;
                margin-top: 10px;
            }
            QGroupBox::title {
                subcontrol-origin: margin;
                left: 0px;
                padding: 0 5px 0 0;
            }
        """)
        data_layout = QVBoxLayout()
        data_layout.setContentsMargins(0, 15, 0, 0)
        data_layout.setSpacing(10)
        
        self.clear_all_button = QPushButton("Clear All Data")
        self.clear_all_button.clicked.connect(self._on_clear_all_data_clicked)
        self.clear_all_button.setFixedHeight(40)
        self.clear_all_button.setCursor(Qt.PointingHandCursor)
        self.clear_all_button.setStyleSheet("""
            QPushButton {
                padding: 10px 20px;
                background-color: white;
                color: #D13438;
                border: 1px solid #E0E0E0;
                border-radius: 8px;
                font-size: 13px;
                font-family: 'Segoe UI', sans-serif;
                font-weight: 600;
                text-align: left;
            }
            QPushButton:hover {
                background-color: #FFF4F4;
                border-color: #D13438;
            }
            QPushButton:pressed {
                background-color: #FFE6E6;
            }
        """)
        data_layout.addWidget(self.clear_all_button)
        
        clear_help = QLabel("This will permanently delete all clipboard history")
        clear_help.setStyleSheet("""
            QLabel {
                color: #D13438;
                font-size: 11px;
                font-family: 'Segoe UI', sans-serif;
                padding: 8px;
                background-color: #FFF4F4;
                border-radius: 6px;
            }
        """)
        data_layout.addWidget(clear_help)
        
        data_group.setLayout(data_layout)
        layout.addWidget(data_group)
        
        layout.addStretch()
        tab.setLayout(layout)
        return tab
    
    def _create_about_tab(self) -> QWidget:
        """Create the About tab."""
        tab = QWidget()
        tab.setStyleSheet("background-color: transparent;")
        
        # Create scroll area
        scroll_area = QScrollArea()
        scroll_area.setWidgetResizable(True)
        scroll_area.setFrameShape(QScrollArea.NoFrame)
        scroll_area.setStyleSheet("""
            QScrollArea {
                background-color: transparent;
                border: none;
            }
            QScrollBar:vertical {
                background-color: transparent;
                width: 8px;
                margin: 0px;
            }
            QScrollBar::handle:vertical {
                background-color: #CCCCCC;
                border-radius: 4px;
                min-height: 30px;
            }
            QScrollBar::handle:vertical:hover {
                background-color: #2B7FD8;
            }
            QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {
                height: 0px;
            }
            QScrollBar::add-page:vertical, QScrollBar::sub-page:vertical {
                background: none;
            }
        """)
        
        # Content widget inside scroll area
        content_widget = QWidget()
        content_widget.setStyleSheet("background-color: transparent;")
        layout = QVBoxLayout()
        layout.setContentsMargins(10, 10, 10, 10)
        layout.setSpacing(12)
        layout.setAlignment(Qt.AlignTop | Qt.AlignHCenter)
        
        # App icon
        from PyQt5.QtGui import QPixmap
        icon_label = QLabel()
        icon_label.setAlignment(Qt.AlignCenter)
        
        # Try to load clipboard.png
        icon_paths = [
            os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'assets', 'icons', 'clipboard.png'),
            'assets/icons/clipboard.png',
        ]
        
        icon_loaded = False
        for icon_path in icon_paths:
            if os.path.exists(icon_path):
                pixmap = QPixmap(icon_path)
                if not pixmap.isNull():
                    scaled_pixmap = pixmap.scaled(64, 64, Qt.KeepAspectRatio, Qt.SmoothTransformation)
                    icon_label.setPixmap(scaled_pixmap)
                    icon_loaded = True
                    break
        
        if not icon_loaded:
            icon_label.setText("📋")
            icon_label.setStyleSheet("font-size: 48px;")
        
        icon_label.setStyleSheet("""
            QLabel {
                margin-bottom: 10px;
            }
        """)
        layout.addWidget(icon_label)
        
        # App name
        app_name = QLabel("Clipboard Manager")
        app_name.setAlignment(Qt.AlignCenter)
        app_name.setStyleSheet("""
            QLabel {
                font-family: 'Segoe UI', sans-serif;
                font-size: 24px;
                font-weight: 600;
                color: #1F1F1F;
            }
        """)
        layout.addWidget(app_name)
        
        # Version
        version = QLabel(f"Version {__version__}")
        version.setAlignment(Qt.AlignCenter)
        version.setStyleSheet("""
            QLabel {
                color: #888888;
                font-size: 13px;
                font-family: 'Segoe UI', sans-serif;
                margin-bottom: 10px;
            }
        """)
        layout.addWidget(version)
        
        # Description
        description = QLabel(
            "A lightweight clipboard manager that saves your copy history and lets you reuse it anytime."
        )
        description.setAlignment(Qt.AlignCenter)
        description.setWordWrap(True)
        description.setMaximumWidth(500)
        description.setStyleSheet("""
            QLabel {
                color: #666666;
                font-size: 12px;
                font-family: 'Segoe UI', sans-serif;
                margin: 10px 20px;
            }
        """)
        layout.addWidget(description)
        
        # Features box with scroll
        features_box = QWidget()
        features_box.setObjectName("featuresBox")
        features_box.setMaximumWidth(500)
        features_box.setStyleSheet("""
            #featuresBox {
                background-color: #F9F9F9;
                border-radius: 8px;
            }
        """)
        features_layout = QVBoxLayout()
        features_layout.setContentsMargins(12, 12, 12, 12)
        features_layout.setSpacing(8)
        
        features_title = QLabel("Features")
        features_title.setStyleSheet("""
            QLabel {
                font-family: 'Segoe UI', sans-serif;
                font-size: 12px;
                font-weight: 600;
                color: #1F1F1F;
                background: transparent;
            }
        """)
        features_layout.addWidget(features_title)
        
        features_text = [
            "• Automatic clipboard monitoring",
            "• Text, links, and images support",
            "• Fast search functionality",
            "• Global hotkey (Ctrl+Shift+V)",
            "• Cross-platform support",
            "• 100% local storage",
            "• Privacy-focused design",
            "• Lightweight and fast",
            "• Modern Windows 11 UI",
            "• System tray integration",
            "• Customizable settings",
            "• Auto-start on system boot"
        ]
        
        for feature in features_text:
            feature_label = QLabel(feature)
            feature_label.setStyleSheet("""
                QLabel {
                    color: #555555;
                    font-size: 11px;
                    font-family: 'Segoe UI', sans-serif;
                    background: transparent;
                    padding: 2px 0px;
                }
            """)
            features_layout.addWidget(feature_label)
        
        features_box.setLayout(features_layout)
        layout.addWidget(features_box)
        
        # License
        license_label = QLabel("License: MIT")
        license_label.setAlignment(Qt.AlignCenter)
        license_label.setStyleSheet("""
            QLabel {
                color: #888888;
                font-size: 11px;
                font-family: 'Segoe UI', sans-serif;
                margin-top: 15px;
            }
        """)
        layout.addWidget(license_label)
        
        layout.addStretch()
        content_widget.setLayout(layout)
        
        # Set content widget to scroll area
        scroll_area.setWidget(content_widget)
        
        # Main tab layout
        tab_layout = QVBoxLayout()
        tab_layout.setContentsMargins(0, 0, 0, 0)
        tab_layout.addWidget(scroll_area)
        tab.setLayout(tab_layout)
        
        return tab
    
    def _load_settings(self):
        """Load current settings from config."""
        # General tab
        self.autostart_checkbox.setChecked(self.config.get('auto_start', False))
        self.hotkey_input.setText(self.config.get('hotkey', 'ctrl+shift+v'))
        
        # Capture tab
        self.capture_text_checkbox.setChecked(self.config.get('capture_text', True))
        self.capture_links_checkbox.setChecked(self.config.get('capture_links', True))
        self.capture_images_checkbox.setChecked(self.config.get('capture_images', True))
        
        # Storage tab
        self.max_items_spinbox.setValue(self.config.get('max_items', 1000))
    
    def _on_capture_hotkey_clicked(self):
        """Handle capture hotkey button click."""
        # Change button text to indicate waiting for input
        self.capture_hotkey_button.setText("Press keys...")
        self.capture_hotkey_button.setEnabled(False)
        
        # Install event filter to capture key combination
        self.hotkey_input.setReadOnly(False)
        self.hotkey_input.setFocus()
        self.hotkey_input.clear()
        self.hotkey_input.installEventFilter(self)
        
        self._capturing_hotkey = True
        self._hotkey_modifiers = []
        self._hotkey_key = None
    
    def eventFilter(self, obj, event):
        """Event filter to capture hotkey combination."""
        if obj == self.hotkey_input and self._capturing_hotkey:
            from PyQt5.QtCore import QEvent
            from PyQt5.QtGui import QKeyEvent
            
            if event.type() == QEvent.KeyPress:
                key_event = event
                key = key_event.key()
                
                # Build modifier list
                modifiers = []
                if key_event.modifiers() & Qt.ControlModifier:
                    modifiers.append('ctrl')
                if key_event.modifiers() & Qt.ShiftModifier:
                    modifiers.append('shift')
                if key_event.modifiers() & Qt.AltModifier:
                    modifiers.append('alt')
                if key_event.modifiers() & Qt.MetaModifier:
                    modifiers.append('super')
                
                # Get key name
                key_name = None
                if key >= Qt.Key_A and key <= Qt.Key_Z:
                    key_name = chr(key).lower()
                elif key >= Qt.Key_0 and key <= Qt.Key_9:
                    key_name = chr(key)
                elif key == Qt.Key_Space:
                    key_name = 'space'
                elif key == Qt.Key_Return or key == Qt.Key_Enter:
                    key_name = 'enter'
                elif key == Qt.Key_Tab:
                    key_name = 'tab'
                elif key == Qt.Key_Escape:
                    # Cancel hotkey capture
                    self._cancel_hotkey_capture()
                    return True
                
                # If we have modifiers and a key, construct hotkey string
                if modifiers and key_name:
                    hotkey_string = '+'.join(modifiers + [key_name])
                    self.hotkey_input.setText(hotkey_string)
                    self._finish_hotkey_capture()
                    return True
        
        return super().eventFilter(obj, event)
    
    def _finish_hotkey_capture(self):
        """Finish hotkey capture."""
        self._capturing_hotkey = False
        self.hotkey_input.removeEventFilter(self)
        self.hotkey_input.setReadOnly(True)
        self.capture_hotkey_button.setText("Change")
        self.capture_hotkey_button.setEnabled(True)
    
    def _cancel_hotkey_capture(self):
        """Cancel hotkey capture."""
        self._capturing_hotkey = False
        self.hotkey_input.removeEventFilter(self)
        self.hotkey_input.setReadOnly(True)
        self.hotkey_input.setText(self.config.get('hotkey', 'ctrl+shift+v'))
        self.capture_hotkey_button.setText("Change")
        self.capture_hotkey_button.setEnabled(True)
    
    def _on_clear_all_data_clicked(self):
        """Handle clear all data button click."""
        reply = QMessageBox.question(
            self,
            'Clear All Data',
            'Are you sure you want to delete all clipboard history?\n\n'
            'This action cannot be undone.',
            QMessageBox.Yes | QMessageBox.No,
            QMessageBox.No
        )
        
        if reply == QMessageBox.Yes:
            self.clear_all_requested.emit()
            QMessageBox.information(
                self,
                'Data Cleared',
                'All clipboard history has been deleted.'
            )
    
    def _on_save_clicked(self):
        """Handle save button click."""
        # Validate hotkey
        hotkey = self.hotkey_input.text().strip()
        if not hotkey:
            QMessageBox.warning(
                self,
                'Invalid Hotkey',
                'Please set a valid hotkey combination.'
            )
            return
        
        # Check if hotkey changed
        old_hotkey = self.config.get('hotkey')
        hotkey_changed = (hotkey != old_hotkey)
        
        # Handle auto-start configuration
        auto_start_enabled = self.autostart_checkbox.isChecked()
        old_auto_start = self.config.get('auto_start', False)
        
        if auto_start_enabled != old_auto_start:
            if auto_start_enabled:
                if not self.autostart_manager.enable_autostart():
                    QMessageBox.warning(
                        self,
                        'Auto-Start Failed',
                        'Failed to enable auto-start. Please check permissions.'
                    )
                    # Revert checkbox state
                    self.autostart_checkbox.setChecked(False)
                    auto_start_enabled = False
            else:
                if not self.autostart_manager.disable_autostart():
                    QMessageBox.warning(
                        self,
                        'Auto-Start Failed',
                        'Failed to disable auto-start.'
                    )
        
        # Save general settings
        self.config.set('auto_start', auto_start_enabled)
        self.config.set('hotkey', hotkey)
        
        # Save capture settings
        capture_text = self.capture_text_checkbox.isChecked()
        capture_links = self.capture_links_checkbox.isChecked()
        capture_images = self.capture_images_checkbox.isChecked()
        
        self.config.set('capture_text', capture_text)
        self.config.set('capture_links', capture_links)
        self.config.set('capture_images', capture_images)
        
        # Save storage settings
        max_items = self.max_items_spinbox.value()
        old_max_items = self.config.get('max_items')
        self.config.set('max_items', max_items)
        
        # Emit signals for specific changes
        if hotkey_changed:
            self.hotkey_changed.emit(hotkey)
        
        capture_settings = {
            'capture_text': capture_text,
            'capture_links': capture_links,
            'capture_images': capture_images
        }
        self.capture_settings_changed.emit(capture_settings)
        
        if max_items != old_max_items:
            self.storage_limit_changed.emit(max_items)
        
        # Emit general settings changed signal
        self.settings_changed.emit(self.config.data.copy())
        
        # Show success message
        QMessageBox.information(
            self,
            'Settings Saved',
            'Your settings have been saved successfully.'
        )
        
        self.close()
    
    def showEvent(self, event):
        """Handle window show event."""
        # Reload settings when window is shown
        self._load_settings()
        super().showEvent(event)
    
    def closeEvent(self, event):
        """Handle window close event."""
        # Reset hotkey capture if active
        if hasattr(self, '_capturing_hotkey') and self._capturing_hotkey:
            self._cancel_hotkey_capture()
        super().closeEvent(event)
