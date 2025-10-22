"""Linux-specific global hotkey implementation."""

import logging
from typing import Callable, Optional
import threading
from utils.platform_utils import get_display_server


class LinuxHotkeyHandler:
    """
    Linux-specific implementation of global hotkey handling.
    
    Uses pynput library for global hotkey registration on Linux.
    Handles both X11 and Wayland display servers.
    """
    
    def __init__(self):
        """Initialize Linux hotkey handler."""
        self.logger = logging.getLogger(self.__class__.__name__)
        self._pynput = None
        self._keyboard = None
        self._listener = None
        self._registered_hotkey = None
        self._callback = None
        self._current_keys = set()
        self._hotkey_combo = None
        
        # Detect display server
        self.display_server = get_display_server()
        self.logger.info(f"Detected display server: {self.display_server}")
        
        # Check if display server is supported
        if self.display_server == 'unknown':
            self.logger.warning("Unknown display server - hotkeys may not work")
        
        try:
            from pynput import keyboard
            self._pynput = keyboard
            self.logger.info("pynput library loaded successfully")
        except ImportError:
            self.logger.error("pynput library not available on this system")
        except Exception as e:
            self.logger.exception(f"Error loading pynput library: {e}")
    
    def register(self, parsed_hotkey: dict, callback: Callable) -> bool:
        """
        Register a global hotkey on Linux.
        
        Args:
            parsed_hotkey: Dictionary with 'modifiers', 'key', and 'original' keys
            callback: Function to call when hotkey is pressed
            
        Returns:
            True if registration successful, False otherwise
        """
        if not self._pynput:
            self.logger.error("pynput library not available")
            return False
        
        # Warn if on Wayland (may have limitations)
        if self.display_server == 'wayland':
            self.logger.warning(
                "Running on Wayland - global hotkeys may have limited functionality"
            )
        
        try:
            # Build hotkey combination
            self._hotkey_combo = self._build_hotkey_combo(parsed_hotkey)
            self._callback = callback
            self._registered_hotkey = parsed_hotkey
            
            self.logger.info(f"Attempting to register Linux hotkey: {parsed_hotkey['original']}")
            
            # Create and start keyboard listener
            self._listener = self._pynput.Listener(
                on_press=self._on_press,
                on_release=self._on_release
            )
            
            # Start listener in background thread
            self._listener.start()
            
            self.logger.info(f"Successfully registered Linux hotkey: {parsed_hotkey['original']}")
            return True
            
        except Exception as e:
            self.logger.exception(f"Error registering Linux hotkey: {e}")
            
            # Provide helpful error messages
            if "display" in str(e).lower():
                self.logger.error(
                    "Display server error. Ensure DISPLAY or WAYLAND_DISPLAY is set."
                )
            elif "permission" in str(e).lower():
                self.logger.error(
                    "Permission denied. May need additional permissions for global hotkeys."
                )
            
            return False
    
    def unregister(self) -> bool:
        """
        Unregister the current global hotkey.
        
        Returns:
            True if unregistration successful, False otherwise
        """
        if not self._registered_hotkey:
            self.logger.debug("No hotkey registered to unregister")
            return True
        
        try:
            # Stop the listener
            if self._listener:
                self._listener.stop()
                self._listener = None
                self.logger.info("Successfully unregistered Linux hotkey")
            
            self._registered_hotkey = None
            self._callback = None
            self._hotkey_combo = None
            self._current_keys.clear()
            return True
            
        except Exception as e:
            self.logger.exception(f"Error unregistering Linux hotkey: {e}")
            return False
    
    def _build_hotkey_combo(self, parsed_hotkey: dict) -> set:
        """
        Build hotkey combination set for pynput.
        
        Args:
            parsed_hotkey: Dictionary with 'modifiers' and 'key'
            
        Returns:
            Set of pynput Key objects representing the hotkey
        """
        combo = set()
        
        # Add modifiers
        for modifier in parsed_hotkey['modifiers']:
            if modifier == 'ctrl':
                combo.add(self._pynput.Key.ctrl_l)
                combo.add(self._pynput.Key.ctrl_r)  # Accept either ctrl key
            elif modifier == 'shift':
                combo.add(self._pynput.Key.shift_l)
                combo.add(self._pynput.Key.shift_r)  # Accept either shift key
            elif modifier == 'alt':
                combo.add(self._pynput.Key.alt_l)
                combo.add(self._pynput.Key.alt_r)  # Accept either alt key
            elif modifier == 'super':
                combo.add(self._pynput.Key.cmd)  # Super/Windows key
        
        # Add key
        key = parsed_hotkey['key']
        
        # Handle special keys
        if key == 'space':
            combo.add(self._pynput.Key.space)
        elif key == 'enter':
            combo.add(self._pynput.Key.enter)
        elif key == 'tab':
            combo.add(self._pynput.Key.tab)
        elif key in ('esc', 'escape'):
            combo.add(self._pynput.Key.esc)
        elif key == 'backspace':
            combo.add(self._pynput.Key.backspace)
        elif key == 'delete':
            combo.add(self._pynput.Key.delete)
        elif key == 'insert':
            combo.add(self._pynput.Key.insert)
        elif key == 'home':
            combo.add(self._pynput.Key.home)
        elif key == 'end':
            combo.add(self._pynput.Key.end)
        elif key == 'pageup':
            combo.add(self._pynput.Key.page_up)
        elif key == 'pagedown':
            combo.add(self._pynput.Key.page_down)
        elif key == 'up':
            combo.add(self._pynput.Key.up)
        elif key == 'down':
            combo.add(self._pynput.Key.down)
        elif key == 'left':
            combo.add(self._pynput.Key.left)
        elif key == 'right':
            combo.add(self._pynput.Key.right)
        elif key.startswith('f') and len(key) <= 3:  # F1-F12
            try:
                f_num = int(key[1:])
                if 1 <= f_num <= 12:
                    combo.add(getattr(self._pynput.Key, f'f{f_num}'))
            except (ValueError, AttributeError):
                pass
        else:
            # Regular character key
            combo.add(self._pynput.KeyCode.from_char(key))
        
        return combo
    
    def _on_press(self, key):
        """
        Handle key press events.
        
        Args:
            key: pynput Key object
        """
        try:
            # Add key to current pressed keys
            self._current_keys.add(key)
            
            # Check if hotkey combination is pressed
            if self._is_hotkey_pressed():
                self.logger.debug("Hotkey combination detected")
                # Call the callback
                if self._callback:
                    # Run callback in separate thread to avoid blocking
                    threading.Thread(target=self._callback, daemon=True).start()
        except Exception as e:
            self.logger.exception(f"Error in key press handler: {e}")
    
    def _on_release(self, key):
        """
        Handle key release events.
        
        Args:
            key: pynput Key object
        """
        try:
            # Remove key from current pressed keys
            self._current_keys.discard(key)
        except Exception as e:
            self.logger.exception(f"Error in key release handler: {e}")
    
    def _is_hotkey_pressed(self) -> bool:
        """
        Check if the registered hotkey combination is currently pressed.
        
        Returns:
            True if hotkey is pressed, False otherwise
        """
        if not self._hotkey_combo:
            return False
        
        # Check if all required keys are pressed
        # For modifiers, we accept either left or right variant
        for required_key in self._hotkey_combo:
            # Check if this specific key is pressed
            if required_key in self._current_keys:
                continue
            
            # For modifiers, check if the opposite variant is pressed
            # (e.g., if ctrl_l is required, check if ctrl_r is pressed)
            found = False
            if hasattr(required_key, 'name'):
                key_name = required_key.name
                if key_name.endswith('_l'):
                    # Check for right variant
                    right_key = getattr(self._pynput.Key, key_name[:-2] + '_r', None)
                    if right_key and right_key in self._current_keys:
                        found = True
                elif key_name.endswith('_r'):
                    # Check for left variant
                    left_key = getattr(self._pynput.Key, key_name[:-2] + '_l', None)
                    if left_key and left_key in self._current_keys:
                        found = True
            
            if not found:
                return False
        
        return True
    
    def __del__(self):
        """Cleanup on deletion."""
        if self._listener:
            self.unregister()
