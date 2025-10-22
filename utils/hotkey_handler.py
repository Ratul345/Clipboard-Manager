"""Global hotkey handler for Clipboard Manager."""

import logging
from typing import Callable, Optional
from utils.platform_utils import is_windows, is_linux


class HotkeyHandler:
    """
    Cross-platform global hotkey handler.
    
    Manages registration and handling of global keyboard shortcuts
    that work even when the application is not in focus.
    """
    
    def __init__(self):
        """Initialize the hotkey handler."""
        self.logger = logging.getLogger(self.__class__.__name__)
        self.current_hotkey = None
        self.callback = None
        self._platform_handler = None
        self._is_registered = False
        
        # Initialize platform-specific handler
        if is_windows():
            from utils.windows_hotkey import WindowsHotkeyHandler
            self._platform_handler = WindowsHotkeyHandler()
            self.logger.info("Initialized Windows hotkey handler")
        elif is_linux():
            from utils.linux_hotkey import LinuxHotkeyHandler
            self._platform_handler = LinuxHotkeyHandler()
            self.logger.info("Initialized Linux hotkey handler")
        else:
            self.logger.warning("Unsupported platform for global hotkeys")
    
    def register_hotkey(self, hotkey: str, callback: Callable) -> bool:
        """
        Register a global hotkey.
        
        Args:
            hotkey: Hotkey string in format "ctrl+shift+v" or "ctrl+alt+c"
            callback: Function to call when hotkey is pressed
            
        Returns:
            True if registration successful, False otherwise
        """
        if not self._platform_handler:
            self.logger.error("No platform handler available for hotkey registration")
            return False
        
        # Parse and validate hotkey string
        parsed_hotkey = self._parse_hotkey(hotkey)
        if not parsed_hotkey:
            self.logger.error(f"Invalid hotkey format: {hotkey}")
            return False
        
        # Unregister existing hotkey if any
        if self._is_registered:
            self.unregister_hotkey()
        
        # Register new hotkey
        try:
            success = self._platform_handler.register(parsed_hotkey, callback)
            if success:
                self.current_hotkey = hotkey
                self.callback = callback
                self._is_registered = True
                self.logger.info(f"Successfully registered hotkey: {hotkey}")
            else:
                self.logger.error(f"Failed to register hotkey: {hotkey}")
            return success
        except Exception as e:
            self.logger.exception(f"Error registering hotkey {hotkey}: {e}")
            return False
    
    def unregister_hotkey(self) -> bool:
        """
        Unregister the current global hotkey.
        
        Returns:
            True if unregistration successful, False otherwise
        """
        if not self._is_registered:
            self.logger.debug("No hotkey registered to unregister")
            return True
        
        if not self._platform_handler:
            self.logger.error("No platform handler available for hotkey unregistration")
            return False
        
        try:
            success = self._platform_handler.unregister()
            if success:
                self.logger.info(f"Successfully unregistered hotkey: {self.current_hotkey}")
                self.current_hotkey = None
                self.callback = None
                self._is_registered = False
            else:
                self.logger.error(f"Failed to unregister hotkey: {self.current_hotkey}")
            return success
        except Exception as e:
            self.logger.exception(f"Error unregistering hotkey: {e}")
            return False
    
    def update_hotkey(self, new_hotkey: str) -> bool:
        """
        Update the registered hotkey to a new combination.
        
        Args:
            new_hotkey: New hotkey string in format "ctrl+shift+v"
            
        Returns:
            True if update successful, False otherwise
        """
        if not self.callback:
            self.logger.error("Cannot update hotkey: no callback registered")
            return False
        
        # Store callback before unregistering
        callback = self.callback
        
        # Unregister old hotkey
        if self._is_registered:
            self.unregister_hotkey()
        
        # Register new hotkey
        success = self.register_hotkey(new_hotkey, callback)
        if success:
            self.logger.info(f"Successfully updated hotkey to: {new_hotkey}")
        else:
            self.logger.error(f"Failed to update hotkey to: {new_hotkey}")
        
        return success
    
    def _parse_hotkey(self, hotkey: str) -> Optional[dict]:
        """
        Parse hotkey string into structured format.
        
        Args:
            hotkey: Hotkey string like "ctrl+shift+v" or "ctrl+alt+c"
            
        Returns:
            Dictionary with parsed hotkey components or None if invalid
        """
        if not hotkey or not isinstance(hotkey, str):
            return None
        
        # Normalize to lowercase and split by +
        parts = [part.strip().lower() for part in hotkey.split('+')]
        
        if len(parts) < 2:
            self.logger.error(f"Hotkey must have at least one modifier and one key: {hotkey}")
            return None
        
        # Separate modifiers and key
        modifiers = []
        key = None
        
        valid_modifiers = {'ctrl', 'control', 'shift', 'alt', 'win', 'cmd', 'super'}
        
        for part in parts[:-1]:
            # Normalize modifier names
            if part in ('ctrl', 'control'):
                modifiers.append('ctrl')
            elif part == 'shift':
                modifiers.append('shift')
            elif part == 'alt':
                modifiers.append('alt')
            elif part in ('win', 'cmd', 'super'):
                modifiers.append('super')
            else:
                self.logger.error(f"Invalid modifier: {part}")
                return None
        
        # Last part is the key
        key = parts[-1]
        
        if not key or len(key) == 0:
            self.logger.error("Hotkey must have a key component")
            return None
        
        # Validate key (basic validation)
        if len(key) > 1 and key not in ('space', 'enter', 'tab', 'esc', 'escape', 
                                         'backspace', 'delete', 'insert', 'home', 
                                         'end', 'pageup', 'pagedown', 'up', 'down', 
                                         'left', 'right', 'f1', 'f2', 'f3', 'f4', 
                                         'f5', 'f6', 'f7', 'f8', 'f9', 'f10', 'f11', 'f12'):
            self.logger.error(f"Invalid key: {key}")
            return None
        
        return {
            'modifiers': modifiers,
            'key': key,
            'original': hotkey
        }
    
    def is_registered(self) -> bool:
        """
        Check if a hotkey is currently registered.
        
        Returns:
            True if hotkey is registered, False otherwise
        """
        return self._is_registered
    
    def get_current_hotkey(self) -> Optional[str]:
        """
        Get the currently registered hotkey string.
        
        Returns:
            Current hotkey string or None if no hotkey registered
        """
        return self.current_hotkey
    
    def __del__(self):
        """Cleanup on deletion."""
        if self._is_registered:
            self.unregister_hotkey()
