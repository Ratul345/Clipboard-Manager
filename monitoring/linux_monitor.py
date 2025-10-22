"""Linux-specific clipboard monitoring implementation."""

import os
import subprocess
import logging
from typing import Optional, Tuple, Any
from io import BytesIO

try:
    from PIL import Image
    PIL_AVAILABLE = True
except ImportError:
    PIL_AVAILABLE = False

try:
    import pyperclip
    PYPERCLIP_AVAILABLE = True
except ImportError:
    PYPERCLIP_AVAILABLE = False

from .clipboard_monitor import ClipboardMonitor


class LinuxClipboardMonitor(ClipboardMonitor):
    """
    Linux-specific implementation of clipboard monitoring.
    
    Supports both X11 and Wayland display servers with fallback to pyperclip
    for basic text support.
    """
    
    def __init__(self, poll_interval: float = 0.5):
        """
        Initialize Linux clipboard monitor.
        
        Args:
            poll_interval: Time in seconds between clipboard checks (default 0.5s)
        """
        super().__init__(poll_interval)
        self.logger = logging.getLogger(self.__class__.__name__)
        self.display_server = self._detect_display_server()
        self.logger.info(f"Detected display server: {self.display_server}")
        
        # Check available clipboard tools
        self._check_clipboard_tools()
    
    def _detect_display_server(self) -> str:
        """
        Detect which display server is running (X11 or Wayland).
        
        Returns:
            'wayland', 'x11', or 'unknown'
        """
        if os.environ.get('WAYLAND_DISPLAY'):
            return 'wayland'
        elif os.environ.get('DISPLAY'):
            return 'x11'
        return 'unknown'
    
    def _check_clipboard_tools(self) -> None:
        """Check which clipboard tools are available on the system."""
        self.has_xclip = self._command_exists('xclip')
        self.has_xsel = self._command_exists('xsel')
        self.has_wl_paste = self._command_exists('wl-paste')
        self.has_wl_copy = self._command_exists('wl-copy')
        
        self.logger.debug(f"Clipboard tools available: xclip={self.has_xclip}, "
                         f"xsel={self.has_xsel}, wl-paste={self.has_wl_paste}, "
                         f"wl-copy={self.has_wl_copy}, pyperclip={PYPERCLIP_AVAILABLE}")
    
    def _command_exists(self, command: str) -> bool:
        """
        Check if a command exists in PATH.
        
        Args:
            command: Command name to check
            
        Returns:
            True if command exists, False otherwise
        """
        try:
            subprocess.run(['which', command], 
                          capture_output=True, 
                          check=True, 
                          timeout=1)
            return True
        except (subprocess.CalledProcessError, subprocess.TimeoutExpired, FileNotFoundError):
            return False
    
    def get_clipboard_content(self) -> Tuple[Optional[Any], Optional[str]]:
        """
        Get current clipboard content and type from Linux clipboard.
        
        Returns:
            Tuple of (content, content_type) where:
            - content: The clipboard content (text string or PIL Image)
            - content_type: 'text', 'link', 'image', or None if clipboard is empty
        """
        # Try to get image first
        image_content = self._get_image_content()
        if image_content:
            return image_content, 'image'
        
        # Try to get text content
        text_content = self._get_text_content()
        if text_content:
            content_type = self._detect_content_type(text_content)
            return text_content, content_type
        
        return None, None
    
    def _get_text_content(self) -> Optional[str]:
        """
        Retrieve text content from Linux clipboard.
        
        Returns:
            Text string or None if retrieval fails
        """
        try:
            if self.display_server == 'wayland' and self.has_wl_paste:
                return self._get_text_wayland()
            elif self.display_server == 'x11':
                if self.has_xclip:
                    return self._get_text_xclip()
                elif self.has_xsel:
                    return self._get_text_xsel()
            
            # Fallback to pyperclip
            if PYPERCLIP_AVAILABLE:
                return self._get_text_pyperclip()
            
            self.logger.warning("No clipboard access method available")
            return None
        
        except Exception as e:
            self.logger.error(f"Failed to get text from clipboard: {e}")
            return None
    
    def _get_text_wayland(self) -> Optional[str]:
        """Get text content using wl-paste (Wayland)."""
        try:
            result = subprocess.run(
                ['wl-paste', '-n'],
                capture_output=True,
                text=True,
                timeout=1
            )
            if result.returncode == 0 and result.stdout:
                return result.stdout
            return None
        except Exception as e:
            self.logger.debug(f"wl-paste failed: {e}")
            return None
    
    def _get_text_xclip(self) -> Optional[str]:
        """Get text content using xclip (X11)."""
        try:
            result = subprocess.run(
                ['xclip', '-selection', 'clipboard', '-o'],
                capture_output=True,
                text=True,
                timeout=1
            )
            if result.returncode == 0 and result.stdout:
                return result.stdout
            return None
        except Exception as e:
            self.logger.debug(f"xclip failed: {e}")
            return None
    
    def _get_text_xsel(self) -> Optional[str]:
        """Get text content using xsel (X11)."""
        try:
            result = subprocess.run(
                ['xsel', '--clipboard', '--output'],
                capture_output=True,
                text=True,
                timeout=1
            )
            if result.returncode == 0 and result.stdout:
                return result.stdout
            return None
        except Exception as e:
            self.logger.debug(f"xsel failed: {e}")
            return None
    
    def _get_text_pyperclip(self) -> Optional[str]:
        """Get text content using pyperclip (fallback)."""
        try:
            content = pyperclip.paste()
            return content if content else None
        except Exception as e:
            self.logger.debug(f"pyperclip failed: {e}")
            return None
    
    def _get_image_content(self) -> Optional[Image.Image]:
        """
        Retrieve image content from Linux clipboard.
        
        Returns:
            PIL Image object or None if retrieval fails
        """
        if not PIL_AVAILABLE:
            return None
        
        try:
            if self.display_server == 'wayland' and self.has_wl_paste:
                return self._get_image_wayland()
            elif self.display_server == 'x11' and self.has_xclip:
                return self._get_image_xclip()
            
            return None
        
        except Exception as e:
            self.logger.error(f"Failed to get image from clipboard: {e}")
            return None
    
    def _get_image_wayland(self) -> Optional[Image.Image]:
        """Get image content using wl-paste (Wayland)."""
        try:
            # Try to get image in PNG format
            result = subprocess.run(
                ['wl-paste', '-t', 'image/png'],
                capture_output=True,
                timeout=2
            )
            
            if result.returncode == 0 and result.stdout:
                image = Image.open(BytesIO(result.stdout))
                return image
            
            return None
        except Exception as e:
            self.logger.debug(f"wl-paste image failed: {e}")
            return None
    
    def _get_image_xclip(self) -> Optional[Image.Image]:
        """Get image content using xclip (X11)."""
        try:
            # Try to get image in PNG format
            result = subprocess.run(
                ['xclip', '-selection', 'clipboard', '-t', 'image/png', '-o'],
                capture_output=True,
                timeout=2
            )
            
            if result.returncode == 0 and result.stdout:
                image = Image.open(BytesIO(result.stdout))
                return image
            
            return None
        except Exception as e:
            self.logger.debug(f"xclip image failed: {e}")
            return None
    
    def _detect_content_type(self, text: str) -> str:
        """
        Detect if text content is a link or regular text.
        
        Args:
            text: Text content to analyze
            
        Returns:
            'link' if content is a URL, 'text' otherwise
        """
        if not text:
            return 'text'
        
        # Check if text starts with common URL schemes
        text_stripped = text.strip()
        if text_stripped.startswith(('http://', 'https://', 'ftp://', 'ftps://')):
            return 'link'
        
        # Check if it looks like a URL without scheme
        if '.' in text_stripped and ' ' not in text_stripped and len(text_stripped) < 500:
            # Simple heuristic: contains dot, no spaces, reasonable length
            if text_stripped.count('.') <= 10:  # Avoid false positives
                return 'link'
        
        return 'text'
    
    def copy_to_clipboard(self, content: Any, content_type: str) -> bool:
        """
        Copy content to Linux clipboard.
        
        Args:
            content: Content to copy (text string or PIL Image)
            content_type: Type of content ('text', 'link', or 'image')
            
        Returns:
            True if successful, False otherwise
        """
        try:
            if content_type in ('text', 'link'):
                return self._copy_text_to_clipboard(content)
            elif content_type == 'image' and PIL_AVAILABLE and isinstance(content, Image.Image):
                return self._copy_image_to_clipboard(content)
            
            return False
        
        except Exception as e:
            self.logger.error(f"Failed to copy to clipboard: {e}")
            return False
    
    def _copy_text_to_clipboard(self, text: str) -> bool:
        """Copy text to clipboard."""
        try:
            if self.display_server == 'wayland' and self.has_wl_copy:
                result = subprocess.run(
                    ['wl-copy'],
                    input=text.encode('utf-8'),
                    timeout=1
                )
                return result.returncode == 0
            
            elif self.display_server == 'x11':
                if self.has_xclip:
                    result = subprocess.run(
                        ['xclip', '-selection', 'clipboard'],
                        input=text.encode('utf-8'),
                        timeout=1
                    )
                    return result.returncode == 0
                elif self.has_xsel:
                    result = subprocess.run(
                        ['xsel', '--clipboard', '--input'],
                        input=text.encode('utf-8'),
                        timeout=1
                    )
                    return result.returncode == 0
            
            # Fallback to pyperclip
            if PYPERCLIP_AVAILABLE:
                pyperclip.copy(text)
                return True
            
            return False
        
        except Exception as e:
            self.logger.error(f"Failed to copy text: {e}")
            return False
    
    def _copy_image_to_clipboard(self, image: Image.Image) -> bool:
        """Copy image to clipboard."""
        try:
            # Convert image to PNG bytes
            output = BytesIO()
            image.save(output, 'PNG')
            png_data = output.getvalue()
            
            if self.display_server == 'wayland' and self.has_wl_copy:
                result = subprocess.run(
                    ['wl-copy', '-t', 'image/png'],
                    input=png_data,
                    timeout=2
                )
                return result.returncode == 0
            
            elif self.display_server == 'x11' and self.has_xclip:
                result = subprocess.run(
                    ['xclip', '-selection', 'clipboard', '-t', 'image/png'],
                    input=png_data,
                    timeout=2
                )
                return result.returncode == 0
            
            return False
        
        except Exception as e:
            self.logger.error(f"Failed to copy image: {e}")
            return False
