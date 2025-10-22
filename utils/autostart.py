"""Auto-start configuration for Windows and Linux."""

import os
import sys
import logging
from pathlib import Path
from typing import Optional
from utils.platform_utils import is_windows, is_linux


class AutoStartManager:
    """Manages application auto-start configuration across platforms."""
    
    def __init__(self, app_name: str = "ClipboardManager", app_path: Optional[str] = None):
        """
        Initialize AutoStartManager.
        
        Args:
            app_name: Name of the application
            app_path: Path to application executable (defaults to current script)
        """
        self.logger = logging.getLogger(self.__class__.__name__)
        self.app_name = app_name
        
        # Determine application path
        if app_path is None:
            # Get the path to the main script or executable
            if getattr(sys, 'frozen', False):
                # Running as compiled executable
                self.app_path = sys.executable
            else:
                # Running as script - use app.py in parent directory
                current_dir = os.path.dirname(os.path.abspath(__file__))
                parent_dir = os.path.dirname(current_dir)
                self.app_path = os.path.join(parent_dir, 'app.py')
        else:
            self.app_path = app_path
        
        self.logger.info(f"AutoStartManager initialized with app_path: {self.app_path}")
    
    def enable_autostart(self) -> bool:
        """
        Enable application auto-start.
        
        Returns:
            True if successful, False otherwise
        """
        try:
            if is_windows():
                return self._enable_autostart_windows()
            elif is_linux():
                return self._enable_autostart_linux()
            else:
                self.logger.error("Unsupported platform for auto-start")
                return False
        except Exception as e:
            self.logger.error(f"Failed to enable auto-start: {e}")
            return False
    
    def disable_autostart(self) -> bool:
        """
        Disable application auto-start.
        
        Returns:
            True if successful, False otherwise
        """
        try:
            if is_windows():
                return self._disable_autostart_windows()
            elif is_linux():
                return self._disable_autostart_linux()
            else:
                self.logger.error("Unsupported platform for auto-start")
                return False
        except Exception as e:
            self.logger.error(f"Failed to disable auto-start: {e}")
            return False
    
    def is_autostart_enabled(self) -> bool:
        """
        Check if auto-start is currently enabled.
        
        Returns:
            True if enabled, False otherwise
        """
        try:
            if is_windows():
                return self._is_autostart_enabled_windows()
            elif is_linux():
                return self._is_autostart_enabled_linux()
            else:
                return False
        except Exception as e:
            self.logger.error(f"Failed to check auto-start status: {e}")
            return False
    
    def _enable_autostart_windows(self) -> bool:
        """Enable auto-start on Windows via registry."""
        try:
            import winreg
            
            # Open registry key for current user startup
            key_path = r"Software\Microsoft\Windows\CurrentVersion\Run"
            key = winreg.OpenKey(
                winreg.HKEY_CURRENT_USER,
                key_path,
                0,
                winreg.KEY_SET_VALUE
            )
            
            # Create command to run
            if self.app_path.endswith('.py'):
                # Running as script - use pythonw to avoid console window
                python_exe = sys.executable.replace('python.exe', 'pythonw.exe')
                if not os.path.exists(python_exe):
                    python_exe = sys.executable
                command = f'"{python_exe}" "{self.app_path}"'
            else:
                # Running as executable
                command = f'"{self.app_path}"'
            
            # Set registry value
            winreg.SetValueEx(
                key,
                self.app_name,
                0,
                winreg.REG_SZ,
                command
            )
            
            winreg.CloseKey(key)
            self.logger.info(f"Auto-start enabled on Windows: {command}")
            return True
        
        except ImportError:
            self.logger.error("winreg module not available (not on Windows)")
            return False
        except Exception as e:
            self.logger.error(f"Failed to enable auto-start on Windows: {e}")
            return False
    
    def _disable_autostart_windows(self) -> bool:
        """Disable auto-start on Windows via registry."""
        try:
            import winreg
            
            # Open registry key for current user startup
            key_path = r"Software\Microsoft\Windows\CurrentVersion\Run"
            key = winreg.OpenKey(
                winreg.HKEY_CURRENT_USER,
                key_path,
                0,
                winreg.KEY_SET_VALUE
            )
            
            # Delete registry value
            try:
                winreg.DeleteValue(key, self.app_name)
                self.logger.info("Auto-start disabled on Windows")
                success = True
            except FileNotFoundError:
                # Value doesn't exist, which is fine
                self.logger.debug("Auto-start registry value not found (already disabled)")
                success = True
            
            winreg.CloseKey(key)
            return success
        
        except ImportError:
            self.logger.error("winreg module not available (not on Windows)")
            return False
        except Exception as e:
            self.logger.error(f"Failed to disable auto-start on Windows: {e}")
            return False
    
    def _is_autostart_enabled_windows(self) -> bool:
        """Check if auto-start is enabled on Windows."""
        try:
            import winreg
            
            # Open registry key for current user startup
            key_path = r"Software\Microsoft\Windows\CurrentVersion\Run"
            key = winreg.OpenKey(
                winreg.HKEY_CURRENT_USER,
                key_path,
                0,
                winreg.KEY_READ
            )
            
            # Try to read the value
            try:
                value, _ = winreg.QueryValueEx(key, self.app_name)
                winreg.CloseKey(key)
                return True
            except FileNotFoundError:
                winreg.CloseKey(key)
                return False
        
        except ImportError:
            return False
        except Exception as e:
            self.logger.error(f"Failed to check auto-start status on Windows: {e}")
            return False
    
    def _enable_autostart_linux(self) -> bool:
        """Enable auto-start on Linux via .desktop file."""
        try:
            # Create autostart directory if it doesn't exist
            autostart_dir = Path.home() / '.config' / 'autostart'
            autostart_dir.mkdir(parents=True, exist_ok=True)
            
            # Create .desktop file path
            desktop_file = autostart_dir / f'{self.app_name}.desktop'
            
            # Determine command to run
            if self.app_path.endswith('.py'):
                # Running as script
                command = f'{sys.executable} {self.app_path}'
            else:
                # Running as executable
                command = self.app_path
            
            # Create .desktop file content
            desktop_content = f"""[Desktop Entry]
Type=Application
Name={self.app_name}
Comment=Clipboard Manager Application
Exec={command}
Icon=clipboard
Terminal=false
Categories=Utility;
X-GNOME-Autostart-enabled=true
"""
            
            # Write .desktop file
            with open(desktop_file, 'w') as f:
                f.write(desktop_content)
            
            # Make it executable
            os.chmod(desktop_file, 0o755)
            
            self.logger.info(f"Auto-start enabled on Linux: {desktop_file}")
            return True
        
        except Exception as e:
            self.logger.error(f"Failed to enable auto-start on Linux: {e}")
            return False
    
    def _disable_autostart_linux(self) -> bool:
        """Disable auto-start on Linux by removing .desktop file."""
        try:
            # Get .desktop file path
            autostart_dir = Path.home() / '.config' / 'autostart'
            desktop_file = autostart_dir / f'{self.app_name}.desktop'
            
            # Remove file if it exists
            if desktop_file.exists():
                desktop_file.unlink()
                self.logger.info(f"Auto-start disabled on Linux: {desktop_file}")
            else:
                self.logger.debug("Auto-start .desktop file not found (already disabled)")
            
            return True
        
        except Exception as e:
            self.logger.error(f"Failed to disable auto-start on Linux: {e}")
            return False
    
    def _is_autostart_enabled_linux(self) -> bool:
        """Check if auto-start is enabled on Linux."""
        try:
            # Check if .desktop file exists
            autostart_dir = Path.home() / '.config' / 'autostart'
            desktop_file = autostart_dir / f'{self.app_name}.desktop'
            
            return desktop_file.exists()
        
        except Exception as e:
            self.logger.error(f"Failed to check auto-start status on Linux: {e}")
            return False
    
    def __repr__(self) -> str:
        """String representation for debugging."""
        enabled = "enabled" if self.is_autostart_enabled() else "disabled"
        return f"AutoStartManager(app_name={self.app_name}, status={enabled})"
