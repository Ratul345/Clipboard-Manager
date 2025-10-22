"""Windows-specific global hotkey implementation."""

import logging
from typing import Callable, Optional
import threading


class WindowsHotkeyHandler:
    """
    Windows-specific implementation of global hotkey handling.
    
    Uses the keyboard library for global hotkey registration on Windows.
    """
    
    def __init__(self):
        """Initialize Windows hotkey handler."""
        self.logger = logging.getLogger(self.__class__.__name__)
        self._keyboard = None
        self._registered_hotkey = None
        self._callback = None
        self._hook = None
        
        try:
            import keyboard
            self._keyboard = keyboard
            self.logger.info("keyboard library loaded successfully")
        except ImportError:
            self.logger.error("keyboard library not available on this system")
        except Exception as e:
            self.logger.exception(f"Error loading keyboard library: {e}")
    
    def register(self, parsed_hotkey: dict, callback: Callable) -> bool:
        """
        Register a global hotkey on Windows.
        
        Args:
            parsed_hotkey: Dictionary with 'modifiers', 'key', and 'original' keys
            callback: Function to call when hotkey is pressed
            
        Returns:
            True if registration successful, False otherwise
        """
        if not self._keyboard:
            self.logger.error("keyboard library not available")
            return False
        
        # Check for admin privileges (keyboard library may need them)
        if not self._check_privileges():
            self.logger.warning("May need administrator privileges for global hotkeys")
            # Continue anyway - keyboard library will handle the error
        
        try:
            # Build hotkey string for keyboard library
            hotkey_str = self._build_hotkey_string(parsed_hotkey)
            
            self.logger.info(f"Attempting to register Windows hotkey: {hotkey_str}")
            
            # Register hotkey with keyboard library
            # Use add_hotkey which works globally
            self._hook = self._keyboard.add_hotkey(
                hotkey_str,
                callback,
                suppress=False  # Don't suppress the key event
            )
            
            self._registered_hotkey = parsed_hotkey
            self._callback = callback
            
            self.logger.info(f"Successfully registered Windows hotkey: {hotkey_str}")
            return True
            
        except ValueError as e:
            self.logger.error(f"Invalid hotkey format: {e}")
            return False
        except Exception as e:
            self.logger.exception(f"Error registering Windows hotkey: {e}")
            
            # Check if it's a permission error
            if "access" in str(e).lower() or "permission" in str(e).lower():
                self.logger.error(
                    "Permission denied. Try running the application as administrator."
                )
            
            return False
    
    def unregister(self) -> bool:
        """
        Unregister the current global hotkey.
        
        Returns:
            True if unregistration successful, False otherwise
        """
        if not self._keyboard:
            self.logger.error("keyboard library not available")
            return False
        
        if not self._registered_hotkey:
            self.logger.debug("No hotkey registered to unregister")
            return True
        
        try:
            # Remove the hotkey hook
            if self._hook is not None:
                self._keyboard.remove_hotkey(self._hook)
                self.logger.info("Successfully unregistered Windows hotkey")
            
            self._registered_hotkey = None
            self._callback = None
            self._hook = None
            return True
            
        except Exception as e:
            self.logger.exception(f"Error unregistering Windows hotkey: {e}")
            return False
    
    def _build_hotkey_string(self, parsed_hotkey: dict) -> str:
        """
        Build hotkey string for keyboard library.
        
        Args:
            parsed_hotkey: Dictionary with 'modifiers' and 'key'
            
        Returns:
            Hotkey string in keyboard library format
        """
        # keyboard library uses '+' to combine keys
        parts = []
        
        # Add modifiers
        for modifier in parsed_hotkey['modifiers']:
            if modifier == 'ctrl':
                parts.append('ctrl')
            elif modifier == 'shift':
                parts.append('shift')
            elif modifier == 'alt':
                parts.append('alt')
            elif modifier == 'super':
                parts.append('win')  # Windows key
        
        # Add key
        key = parsed_hotkey['key']
        parts.append(key)
        
        return '+'.join(parts)
    
    def _check_privileges(self) -> bool:
        """
        Check if the application has necessary privileges.
        
        Returns:
            True if running with sufficient privileges, False otherwise
        """
        try:
            import ctypes
            # Check if running as administrator
            is_admin = ctypes.windll.shell32.IsUserAnAdmin()
            if not is_admin:
                self.logger.warning("Not running as administrator")
            return is_admin
        except Exception as e:
            self.logger.debug(f"Could not check admin privileges: {e}")
            return False
    
    def __del__(self):
        """Cleanup on deletion."""
        if self._registered_hotkey:
            self.unregister()
