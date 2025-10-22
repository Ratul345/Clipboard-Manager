"""
Clipboard Manager - Main Application Entry Point

A cross-platform desktop application that monitors and stores clipboard history,
allowing users to search, browse, and reuse previously copied items.
"""

import sys
import logging
from PyQt5.QtWidgets import QApplication, QSystemTrayIcon
from version import __version__, APP_NAME
from utils.platform_utils import (
    get_operating_system,
    get_display_server,
    ensure_directories_exist,
    get_log_file_path,
    is_windows,
    is_linux
)


def setup_logging():
    """Configure application logging."""
    # Ensure directories exist before creating log file
    ensure_directories_exist()
    
    log_file = get_log_file_path()
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        handlers=[
            logging.FileHandler(log_file),
            logging.StreamHandler(sys.stdout)
        ]
    )
    return logging.getLogger(__name__)


def check_platform_compatibility():
    """
    Check if the current platform is supported.
    
    Returns:
        tuple: (is_supported, message)
    """
    os_type = get_operating_system()
    
    if os_type == 'unknown':
        return False, "Unsupported operating system. Only Windows and Linux are supported."
    
    if is_linux():
        display_server = get_display_server()
        if display_server == 'unknown':
            return False, "Could not detect display server on Linux. X11 or Wayland required."
    
    return True, f"Running on {os_type}"


class ClipboardManagerApp:
    """Main application class that coordinates all components."""
    
    def __init__(self):
        """Initialize the clipboard manager application."""
        self.logger = logging.getLogger(self.__class__.__name__)
        self.qt_app = None
        
        # Initialize component references
        self.storage_manager = None
        self.clipboard_service = None
        self.hotkey_handler = None
        self.main_window = None
        self.system_tray = None
        self.config_manager = None
        self.settings_window = None
        self.autostart_manager = None
    
    def initialize(self):
        """Initialize all application components."""
        self.logger.info("Initializing Clipboard Manager...")
        
        try:
            # Ensure required directories exist
            ensure_directories_exist()
            self.logger.info("Application directories created/verified")
        except Exception as e:
            self.logger.error(f"Failed to create application directories: {e}")
            raise RuntimeError(f"Could not create required directories: {e}")
        
        # Initialize Qt application
        self.qt_app = QApplication(sys.argv)
        self.qt_app.setApplicationName(APP_NAME)
        self.qt_app.setApplicationVersion(__version__)
        self.qt_app.setQuitOnLastWindowClosed(False)  # Keep running in system tray
        
        # Set application icon
        self._set_application_icon()
        
        self.logger.info("Qt application initialized")
        
        # Initialize components
        try:
            from models.config import Config
            self.config_manager = Config()
            self.logger.info("Config manager initialized")
        except Exception as e:
            self.logger.error(f"Failed to initialize config manager: {e}")
            raise RuntimeError(f"Could not load configuration: {e}")
        
        try:
            from storage.storage_manager import StorageManager
            from storage.image_storage import ImageStorage
            self.storage_manager = StorageManager()
            self.image_storage = ImageStorage()
            self.logger.info("Storage manager initialized")
        except Exception as e:
            self.logger.error(f"Failed to initialize storage manager: {e}")
            raise RuntimeError(f"Could not initialize database: {e}")
        
        try:
            from search.search_engine import SearchEngine
            self.search_engine = SearchEngine()
            self.logger.info("Search engine initialized")
            
            from ui.main_window import MainWindow
            self.main_window = MainWindow(self.storage_manager, self.search_engine)
            self.logger.info("Main window initialized")
        except Exception as e:
            self.logger.error(f"Failed to initialize UI components: {e}")
            raise RuntimeError(f"Could not create user interface: {e}")
        
        try:
            from monitoring.clipboard_service import ClipboardService
            max_items = self.config_manager.get('max_items', 1000)
            capture_text = self.config_manager.get('capture_text', True)
            capture_images = self.config_manager.get('capture_images', True)
            capture_links = self.config_manager.get('capture_links', True)
            self.clipboard_service = ClipboardService(
                storage_manager=self.storage_manager,
                image_storage=self.image_storage,
                max_items=max_items,
                capture_text=capture_text,
                capture_images=capture_images,
                capture_links=capture_links
            )
            self.logger.info("Clipboard service initialized")
        except Exception as e:
            self.logger.error(f"Failed to initialize clipboard service: {e}")
            raise RuntimeError(f"Could not start clipboard monitoring: {e}")
        
        try:
            from ui.system_tray import SystemTray
            self.system_tray = SystemTray()
            self._connect_system_tray()
            self.logger.info("System tray initialized")
        except Exception as e:
            self.logger.error(f"Failed to initialize system tray: {e}")
            raise RuntimeError(f"Could not create system tray icon: {e}")
        
        try:
            from utils.hotkey_handler import HotkeyHandler
            self.hotkey_handler = HotkeyHandler()
            self._register_hotkey()
            self.logger.info("Hotkey handler initialized")
        except Exception as e:
            self.logger.error(f"Failed to initialize hotkey handler: {e}")
            # Don't raise - hotkey is optional, user can still use tray
            self.logger.warning("Continuing without global hotkey support")
        
        try:
            from ui.settings_window import SettingsWindow
            self.settings_window = SettingsWindow(self.config_manager)
            self._connect_settings_window()
            self.logger.info("Settings window initialized")
        except Exception as e:
            self.logger.error(f"Failed to initialize settings window: {e}")
            # Don't raise - settings is optional
            self.logger.warning("Continuing without settings window")
        
        try:
            from utils.autostart import AutoStartManager
            self.autostart_manager = AutoStartManager()
            self._verify_autostart()
            self.logger.info("Auto-start manager initialized")
        except Exception as e:
            self.logger.error(f"Failed to initialize auto-start manager: {e}")
            # Don't raise - auto-start is optional
            self.logger.warning("Continuing without auto-start support")
        
        self.logger.info("Clipboard Manager initialization complete")
    
    def _set_application_icon(self):
        """Set the application icon globally."""
        import os
        from PyQt5.QtGui import QIcon
        
        # Try multiple possible icon locations
        possible_paths = [
            os.path.join(os.path.dirname(os.path.abspath(__file__)), 'assets', 'icons', 'clipboard.png'),
            os.path.join(sys._MEIPASS, 'assets', 'icons', 'clipboard.png') if getattr(sys, 'frozen', False) else None,
            'assets/icons/clipboard.png',
        ]
        
        for path in possible_paths:
            if path and os.path.exists(path):
                self.qt_app.setWindowIcon(QIcon(path))
                self.logger.info(f"Application icon set from: {path}")
                return
        
        self.logger.warning("Application icon file not found")
    
    def _verify_autostart(self):
        """Verify and synchronize auto-start configuration."""
        if not self.autostart_manager or not self.config_manager:
            return
        
        # Get the desired auto-start state from config
        auto_start_enabled = self.config_manager.get('auto_start', False)
        
        # Check the actual auto-start state
        actual_state = self.autostart_manager.is_autostart_enabled()
        
        self.logger.info(f"Auto-start config: {auto_start_enabled}, actual: {actual_state}")
        
        # Synchronize if they don't match
        if auto_start_enabled and not actual_state:
            self.logger.info("Enabling auto-start to match configuration")
            if self.autostart_manager.enable_autostart():
                self.logger.info("Auto-start enabled successfully")
            else:
                self.logger.warning("Failed to enable auto-start")
                # Update config to reflect actual state
                self.config_manager.set('auto_start', False)
        elif not auto_start_enabled and actual_state:
            self.logger.info("Disabling auto-start to match configuration")
            if self.autostart_manager.disable_autostart():
                self.logger.info("Auto-start disabled successfully")
            else:
                self.logger.warning("Failed to disable auto-start")
    
    def _connect_system_tray(self):
        """Connect system tray signals to application handlers."""
        if self.system_tray and self.main_window:
            # Connect tray signals
            self.system_tray.open_requested.connect(self._on_tray_open_requested)
            self.system_tray.settings_requested.connect(self._on_tray_settings_requested)
            self.system_tray.exit_requested.connect(self._on_tray_exit_requested)
            
            # Connect main window visibility signal to update tray state
            self.main_window.visibility_changed.connect(self.system_tray.set_window_state)
    
    def _connect_settings_window(self):
        """Connect settings window signals to application handlers."""
        if not self.settings_window:
            return
        
        # Connect settings changed signals
        self.settings_window.hotkey_changed.connect(self._on_hotkey_changed)
        self.settings_window.capture_settings_changed.connect(self._on_capture_settings_changed)
        self.settings_window.storage_limit_changed.connect(self._on_storage_limit_changed)
        self.settings_window.clear_all_requested.connect(self._on_clear_all_requested)
    
    def _on_hotkey_changed(self, new_hotkey: str):
        """Handle hotkey change from settings."""
        self.logger.info(f"Hotkey changed to: {new_hotkey}")
        
        if self.hotkey_handler:
            success = self.hotkey_handler.update_hotkey(new_hotkey)
            
            if success:
                self.logger.info(f"Hotkey successfully updated to: {new_hotkey}")
            else:
                self.logger.error(f"Failed to update hotkey to: {new_hotkey}")
                if self.system_tray:
                    self.system_tray.show_message(
                        "Hotkey Update Failed",
                        f"Could not register new hotkey '{new_hotkey}'.",
                        QSystemTrayIcon.Warning
                    )
    
    def _on_capture_settings_changed(self, settings: dict):
        """Handle capture settings change from settings."""
        self.logger.info(f"Capture settings changed: {settings}")
        
        if self.clipboard_service:
            self.clipboard_service.set_capture_settings(
                capture_text=settings.get('capture_text'),
                capture_images=settings.get('capture_images'),
                capture_links=settings.get('capture_links')
            )
    
    def _on_storage_limit_changed(self, new_limit: int):
        """Handle storage limit change from settings."""
        self.logger.info(f"Storage limit changed to: {new_limit}")
        
        if self.clipboard_service:
            self.clipboard_service.set_max_items(new_limit)
    
    def _on_clear_all_requested(self):
        """Handle clear all data request from settings."""
        self.logger.info("Clear all data requested")
        
        if self.storage_manager:
            success = self.storage_manager.clear_all_items()
            
            if success:
                self.logger.info("All clipboard data cleared")
                # Refresh main window if visible
                if self.main_window and self.main_window.isVisible():
                    self.main_window.load_items()
            else:
                self.logger.error("Failed to clear clipboard data")
    
    def _on_tray_open_requested(self):
        """Handle open request from system tray."""
        if self.main_window:
            if self.main_window.isVisible():
                self.main_window.hide()
                if self.system_tray:
                    self.system_tray.set_window_state(False)
            else:
                self.main_window.show()
                if self.system_tray:
                    self.system_tray.set_window_state(True)
    
    def _on_tray_settings_requested(self):
        """Handle settings request from system tray."""
        self.logger.info("Settings requested")
        if self.settings_window:
            self.settings_window.show()
            self.settings_window.activateWindow()
            self.settings_window.raise_()
    
    def _on_tray_exit_requested(self):
        """Handle exit request from system tray."""
        self.logger.info("Exit requested from system tray")
        self.shutdown()
        if self.qt_app:
            self.qt_app.quit()
    
    def _register_hotkey(self):
        """Register the global hotkey from config."""
        if not self.hotkey_handler:
            self.logger.error("Hotkey handler not initialized")
            return
        
        # Get hotkey from config (default: ctrl+shift+v)
        hotkey = self.config_manager.get('hotkey', 'ctrl+shift+v')
        
        # Register hotkey with toggle window callback
        success = self.hotkey_handler.register_hotkey(hotkey, self._on_hotkey_pressed)
        
        if success:
            self.logger.info(f"Global hotkey registered: {hotkey}")
        else:
            self.logger.error(f"Failed to register global hotkey: {hotkey}")
            # Show notification to user
            if self.system_tray:
                from PyQt5.QtWidgets import QSystemTrayIcon
                self.system_tray.show_message(
                    "Hotkey Registration Failed",
                    f"Could not register hotkey '{hotkey}'. You can still use the system tray to open the application.",
                    QSystemTrayIcon.Warning
                )
    
    def _on_hotkey_pressed(self):
        """Handle global hotkey press - toggle main window visibility."""
        self.logger.debug("Global hotkey pressed")
        
        if self.main_window:
            # Toggle window visibility
            if self.main_window.isVisible():
                self.main_window.hide()
                if self.system_tray:
                    self.system_tray.set_window_state(False)
            else:
                self.main_window.show()
                self.main_window.activateWindow()  # Bring to front
                self.main_window.raise_()  # Ensure it's on top
                if self.system_tray:
                    self.system_tray.set_window_state(True)
    
    def run(self):
        """Start the application main loop."""
        self.logger.info("Starting Clipboard Manager...")
        
        if self.clipboard_service:
            try:
                if self.clipboard_service.start():
                    self.logger.info("Clipboard monitoring started")
                else:
                    self.logger.error("Failed to start clipboard monitoring")
                    if self.system_tray:
                        self.system_tray.show_message(
                            "Clipboard Monitoring Error",
                            "Failed to start clipboard monitoring. Some features may not work.",
                            QSystemTrayIcon.Warning
                        )
            except Exception as e:
                self.logger.error(f"Error starting clipboard monitoring: {e}")
                if self.system_tray:
                    self.system_tray.show_message(
                        "Clipboard Monitoring Error",
                        f"Error starting clipboard monitoring: {e}",
                        QSystemTrayIcon.Warning
                    )
        
        if self.system_tray:
            try:
                self.system_tray.show()
                self.logger.info("System tray icon displayed")
            except Exception as e:
                self.logger.error(f"Failed to show system tray icon: {e}")
                # This is critical - without tray, user can't access the app
                raise RuntimeError(f"Could not display system tray icon: {e}")
        
        # Don't show main window on startup - it will be opened via tray or hotkey
        # The application now runs in the background
        
        # Start Qt event loop
        return self.qt_app.exec_()
    
    def shutdown(self):
        """Perform graceful shutdown of all components."""
        self.logger.info("Shutting down Clipboard Manager...")
        
        try:
            if self.clipboard_service:
                self.clipboard_service.stop()
                self.logger.info("Clipboard monitoring stopped")
        except Exception as e:
            self.logger.error(f"Error stopping clipboard service: {e}")
        
        try:
            if self.hotkey_handler:
                self.hotkey_handler.unregister_hotkey()
                self.logger.info("Global hotkey unregistered")
        except Exception as e:
            self.logger.error(f"Error unregistering hotkey: {e}")
        
        try:
            if self.config_manager:
                self.config_manager.save_config()
                self.logger.info("Configuration saved")
        except Exception as e:
            self.logger.error(f"Error saving configuration: {e}")
        
        try:
            if self.storage_manager:
                self.storage_manager.close()
                self.logger.info("Database connection closed")
        except Exception as e:
            self.logger.error(f"Error closing database: {e}")
        
        self.logger.info("Clipboard Manager shutdown complete")


def main():
    """Main entry point for the application."""
    # Setup logging
    logger = setup_logging()
    logger.info("=" * 60)
    logger.info(f"{APP_NAME} v{__version__} Starting")
    logger.info("=" * 60)
    
    # Check platform compatibility
    is_supported, message = check_platform_compatibility()
    logger.info(f"Platform check: {message}")
    
    if not is_supported:
        logger.error(f"Platform not supported: {message}")
        print(f"ERROR: {message}")
        return 1
    
    # Log platform information
    os_type = get_operating_system()
    logger.info(f"Operating System: {os_type}")
    
    if is_linux():
        display_server = get_display_server()
        logger.info(f"Display Server: {display_server}")
    
    try:
        # Create and initialize application
        app = ClipboardManagerApp()
        app.initialize()
        
        # Run application
        exit_code = app.run()
        
        # Cleanup
        app.shutdown()
        
        return exit_code
    
    except KeyboardInterrupt:
        logger.info("Application interrupted by user")
        return 0
    
    except Exception as e:
        logger.exception(f"Fatal error: {e}")
        print(f"FATAL ERROR: {e}")
        
        # Try to show error notification if Qt is available
        try:
            from PyQt5.QtWidgets import QApplication, QMessageBox
            if QApplication.instance():
                QMessageBox.critical(
                    None,
                    "Clipboard Manager - Fatal Error",
                    f"The application encountered a fatal error and must close:\n\n{str(e)}\n\nCheck the log file for details."
                )
        except:
            pass  # If Qt isn't available, just log the error
        
        return 1


if __name__ == "__main__":
    sys.exit(main())
