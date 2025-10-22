"""Settings window for Clipboard Manager configuration."""

import sys
import os
from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QTabWidget, QLabel,
    QCheckBox, QPushButton, QLineEdit, QSpinBox, QMessageBox,
    QGroupBox, QFormLayout
)
from PyQt5.QtCore import Qt, pyqtSignal
from PyQt5.QtGui import QFont

# Add parent directory to path to import modules
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from models.config import Config
from utils.autostart import AutoStartManager


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
        self.setWindowTitle("Settings - Clipboard Manager")
        self.setFixedSize(500, 500)
        # Set window to always-on-top so it appears above the main window
        self.setWindowFlags(Qt.Window | Qt.WindowStaysOnTopHint)
        
        # Main layout
        main_layout = QVBoxLayout()
        main_layout.setContentsMargins(10, 10, 10, 10)
        
        # Tab widget
        self.tab_widget = QTabWidget()
        
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
        
        main_layout.addWidget(self.tab_widget)
        
        # Button layout
        button_layout = QHBoxLayout()
        button_layout.addStretch()
        
        # Save button
        self.save_button = QPushButton("Save")
        self.save_button.clicked.connect(self._on_save_clicked)
        self.save_button.setStyleSheet("""
            QPushButton {
                padding: 8px 20px;
                background-color: #4CAF50;
                color: white;
                border: none;
                border-radius: 4px;
                font-size: 14px;
            }
            QPushButton:hover {
                background-color: #45a049;
            }
        """)
        button_layout.addWidget(self.save_button)
        
        # Cancel button
        self.cancel_button = QPushButton("Cancel")
        self.cancel_button.clicked.connect(self.close)
        self.cancel_button.setStyleSheet("""
            QPushButton {
                padding: 8px 20px;
                background-color: #f44336;
                color: white;
                border: none;
                border-radius: 4px;
                font-size: 14px;
            }
            QPushButton:hover {
                background-color: #da190b;
            }
        """)
        button_layout.addWidget(self.cancel_button)
        
        main_layout.addLayout(button_layout)
        
        self.setLayout(main_layout)
    
    def _create_general_tab(self) -> QWidget:
        """Create the General settings tab."""
        tab = QWidget()
        layout = QVBoxLayout()
        layout.setContentsMargins(15, 15, 15, 15)
        layout.setSpacing(15)
        
        # Auto-start group
        autostart_group = QGroupBox("Startup")
        autostart_layout = QVBoxLayout()
        
        self.autostart_checkbox = QCheckBox("Launch on system startup")
        autostart_layout.addWidget(self.autostart_checkbox)
        
        autostart_group.setLayout(autostart_layout)
        layout.addWidget(autostart_group)
        
        # Hotkey group
        hotkey_group = QGroupBox("Hotkey")
        hotkey_layout = QFormLayout()
        
        self.hotkey_input = QLineEdit()
        self.hotkey_input.setPlaceholderText("e.g., ctrl+shift+v")
        self.hotkey_input.setReadOnly(True)  # Will be editable via capture button
        
        hotkey_input_layout = QHBoxLayout()
        hotkey_input_layout.addWidget(self.hotkey_input)
        
        self.capture_hotkey_button = QPushButton("Change")
        self.capture_hotkey_button.clicked.connect(self._on_capture_hotkey_clicked)
        hotkey_input_layout.addWidget(self.capture_hotkey_button)
        
        hotkey_widget = QWidget()
        hotkey_widget.setLayout(hotkey_input_layout)
        
        hotkey_layout.addRow("Global hotkey:", hotkey_widget)
        
        hotkey_help = QLabel("Press the button and then press your desired key combination")
        hotkey_help.setStyleSheet("color: #666; font-size: 11px;")
        hotkey_layout.addRow("", hotkey_help)
        
        hotkey_group.setLayout(hotkey_layout)
        layout.addWidget(hotkey_group)
        
        layout.addStretch()
        tab.setLayout(layout)
        return tab
    
    def _create_capture_tab(self) -> QWidget:
        """Create the Capture settings tab."""
        tab = QWidget()
        layout = QVBoxLayout()
        layout.setContentsMargins(15, 15, 15, 15)
        layout.setSpacing(15)
        
        # Content types group
        content_group = QGroupBox("Content Types to Capture")
        content_layout = QVBoxLayout()
        
        self.capture_text_checkbox = QCheckBox("Text")
        self.capture_text_checkbox.setToolTip("Capture plain text from clipboard")
        content_layout.addWidget(self.capture_text_checkbox)
        
        self.capture_links_checkbox = QCheckBox("Links")
        self.capture_links_checkbox.setToolTip("Capture URLs and web links")
        content_layout.addWidget(self.capture_links_checkbox)
        
        self.capture_images_checkbox = QCheckBox("Images")
        self.capture_images_checkbox.setToolTip("Capture images from clipboard")
        content_layout.addWidget(self.capture_images_checkbox)
        
        content_group.setLayout(content_layout)
        layout.addWidget(content_group)
        
        # Info label
        info_label = QLabel("Changes will be applied immediately")
        info_label.setStyleSheet("color: #666; font-size: 11px; margin-top: 10px;")
        layout.addWidget(info_label)
        
        layout.addStretch()
        tab.setLayout(layout)
        return tab
    
    def _create_storage_tab(self) -> QWidget:
        """Create the Storage settings tab."""
        tab = QWidget()
        layout = QVBoxLayout()
        layout.setContentsMargins(15, 15, 15, 15)
        layout.setSpacing(15)
        
        # Storage limit group
        limit_group = QGroupBox("Storage Limit")
        limit_layout = QFormLayout()
        
        self.max_items_spinbox = QSpinBox()
        self.max_items_spinbox.setMinimum(10)
        self.max_items_spinbox.setMaximum(10000)
        self.max_items_spinbox.setSingleStep(100)
        self.max_items_spinbox.setSuffix(" items")
        
        limit_layout.addRow("Maximum items:", self.max_items_spinbox)
        
        limit_help = QLabel("Oldest items will be automatically deleted when limit is reached")
        limit_help.setStyleSheet("color: #666; font-size: 11px;")
        limit_layout.addRow("", limit_help)
        
        limit_group.setLayout(limit_layout)
        layout.addWidget(limit_group)
        
        # Data management group
        data_group = QGroupBox("Data Management")
        data_layout = QVBoxLayout()
        
        self.clear_all_button = QPushButton("Clear All Data")
        self.clear_all_button.clicked.connect(self._on_clear_all_data_clicked)
        self.clear_all_button.setStyleSheet("""
            QPushButton {
                padding: 8px 15px;
                background-color: #f44336;
                color: white;
                border: none;
                border-radius: 4px;
            }
            QPushButton:hover {
                background-color: #d32f2f;
            }
        """)
        data_layout.addWidget(self.clear_all_button)
        
        clear_help = QLabel("This will permanently delete all clipboard history")
        clear_help.setStyleSheet("color: #666; font-size: 11px;")
        data_layout.addWidget(clear_help)
        
        data_group.setLayout(data_layout)
        layout.addWidget(data_group)
        
        layout.addStretch()
        tab.setLayout(layout)
        return tab
    
    def _create_about_tab(self) -> QWidget:
        """Create the About tab."""
        tab = QWidget()
        layout = QVBoxLayout()
        layout.setContentsMargins(15, 15, 15, 15)
        layout.setSpacing(20)
        layout.setAlignment(Qt.AlignTop | Qt.AlignHCenter)
        
        # App name
        app_name = QLabel("Clipboard Manager")
        app_name.setAlignment(Qt.AlignCenter)
        font = QFont()
        font.setPointSize(18)
        font.setBold(True)
        app_name.setFont(font)
        layout.addWidget(app_name)
        
        # Version
        version = QLabel("Version 1.0.0")
        version.setAlignment(Qt.AlignCenter)
        version.setStyleSheet("color: #666; font-size: 14px;")
        layout.addWidget(version)
        
        # Description
        description = QLabel(
            "A cross-platform clipboard manager that captures and stores\n"
            "clipboard history for easy access and reuse."
        )
        description.setAlignment(Qt.AlignCenter)
        description.setWordWrap(True)
        description.setStyleSheet("margin-top: 20px; margin-bottom: 20px;")
        layout.addWidget(description)
        
        # Features
        features_label = QLabel("Features:")
        features_label.setStyleSheet("font-weight: bold; margin-top: 10px;")
        layout.addWidget(features_label)
        
        features = QLabel(
            "• Automatic clipboard monitoring\n"
            "• Support for text, links, and images\n"
            "• Fast search functionality\n"
            "• Global hotkey access\n"
            "• Cross-platform (Windows & Linux)"
        )
        features.setStyleSheet("margin-left: 20px;")
        layout.addWidget(features)
        
        # License
        license_label = QLabel("License: MIT")
        license_label.setAlignment(Qt.AlignCenter)
        license_label.setStyleSheet("color: #666; font-size: 11px; margin-top: 30px;")
        layout.addWidget(license_label)
        
        layout.addStretch()
        tab.setLayout(layout)
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
