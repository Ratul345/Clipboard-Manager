"""Windows-specific clipboard monitoring implementation."""

import time
import logging
from typing import Optional, Tuple, Any
from io import BytesIO

try:
    import win32clipboard
    import win32con
    from PIL import Image
    WINDOWS_AVAILABLE = True
except ImportError:
    WINDOWS_AVAILABLE = False

from .clipboard_monitor import ClipboardMonitor


class WindowsClipboardMonitor(ClipboardMonitor):
    """
    Windows-specific implementation of clipboard monitoring.
    
    Uses win32clipboard for native Windows clipboard access with support
    for text and image content.
    """
    
    def __init__(self, poll_interval: float = 0.5, max_retries: int = 3, retry_delay: float = 0.1):
        """
        Initialize Windows clipboard monitor.
        
        Args:
            poll_interval: Time in seconds between clipboard checks (default 0.5s)
            max_retries: Maximum number of retry attempts for clipboard access (default 3)
            retry_delay: Delay in seconds between retry attempts (default 0.1s)
        """
        if not WINDOWS_AVAILABLE:
            raise ImportError("Windows clipboard monitoring requires pywin32 package")
        
        super().__init__(poll_interval)
        self.max_retries = max_retries
        self.retry_delay = retry_delay
        self.logger = logging.getLogger(self.__class__.__name__)
    
    def get_clipboard_content(self) -> Tuple[Optional[Any], Optional[str]]:
        """
        Get current clipboard content and type from Windows clipboard.
        
        Attempts to retrieve clipboard content with retry logic to handle
        cases where clipboard is locked by another application.
        
        Returns:
            Tuple of (content, content_type) where:
            - content: The clipboard content (text string or PIL Image)
            - content_type: 'text', 'link', 'image', or None if clipboard is empty
        """
        for attempt in range(self.max_retries):
            try:
                win32clipboard.OpenClipboard()
                
                try:
                    # Try to get image first (CF_DIB format)
                    if win32clipboard.IsClipboardFormatAvailable(win32con.CF_DIB):
                        image_content = self._get_image_content()
                        if image_content:
                            return image_content, 'image'
                    
                    # Try to get text content
                    if win32clipboard.IsClipboardFormatAvailable(win32con.CF_UNICODETEXT):
                        text_content = win32clipboard.GetClipboardData(win32con.CF_UNICODETEXT)
                        if text_content:
                            # Detect if it's a link
                            content_type = self._detect_content_type(text_content)
                            return text_content, content_type
                    
                    # Try CF_TEXT as fallback
                    if win32clipboard.IsClipboardFormatAvailable(win32con.CF_TEXT):
                        text_content = win32clipboard.GetClipboardData(win32con.CF_TEXT)
                        if text_content:
                            # Decode bytes to string
                            if isinstance(text_content, bytes):
                                text_content = text_content.decode('utf-8', errors='ignore')
                            content_type = self._detect_content_type(text_content)
                            return text_content, content_type
                    
                    # Clipboard is empty or contains unsupported format
                    return None, None
                
                finally:
                    win32clipboard.CloseClipboard()
            
            except Exception as e:
                if attempt < self.max_retries - 1:
                    self.logger.debug(f"Clipboard access attempt {attempt + 1} failed: {e}, retrying...")
                    time.sleep(self.retry_delay)
                else:
                    self.logger.error(f"Failed to access clipboard after {self.max_retries} attempts: {e}")
                    return None, None
        
        return None, None
    
    def _get_image_content(self) -> Optional[Image.Image]:
        """
        Retrieve image content from Windows clipboard in CF_DIB format.
        
        Returns:
            PIL Image object or None if retrieval fails
        """
        try:
            # Get DIB (Device Independent Bitmap) data
            dib_data = win32clipboard.GetClipboardData(win32con.CF_DIB)
            
            if not dib_data:
                return None
            
            # DIB format: BITMAPINFOHEADER + color table + pixel data
            # We need to convert this to a format PIL can understand
            
            # Create a BMP file in memory by adding BMP file header
            # BMP file header is 14 bytes
            bmp_header = b'BM'  # Signature
            bmp_header += len(dib_data).to_bytes(4, byteorder='little')  # File size
            bmp_header += b'\x00\x00'  # Reserved
            bmp_header += b'\x00\x00'  # Reserved
            bmp_header += b'\x36\x00\x00\x00'  # Offset to pixel data (54 bytes typically)
            
            # Combine header with DIB data
            bmp_data = bmp_header + dib_data
            
            # Load image from bytes
            image = Image.open(BytesIO(bmp_data))
            
            return image
        
        except Exception as e:
            self.logger.error(f"Failed to retrieve image from clipboard: {e}")
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
        Copy content to Windows clipboard.
        
        Args:
            content: Content to copy (text string or PIL Image)
            content_type: Type of content ('text', 'link', or 'image')
            
        Returns:
            True if successful, False otherwise
        """
        for attempt in range(self.max_retries):
            try:
                win32clipboard.OpenClipboard()
                
                try:
                    win32clipboard.EmptyClipboard()
                    
                    if content_type in ('text', 'link'):
                        win32clipboard.SetClipboardData(win32con.CF_UNICODETEXT, content)
                    elif content_type == 'image' and isinstance(content, Image.Image):
                        # Convert PIL Image to DIB format
                        self._set_image_to_clipboard(content)
                    else:
                        return False
                    
                    return True
                
                finally:
                    win32clipboard.CloseClipboard()
            
            except Exception as e:
                if attempt < self.max_retries - 1:
                    self.logger.debug(f"Clipboard write attempt {attempt + 1} failed: {e}, retrying...")
                    time.sleep(self.retry_delay)
                else:
                    self.logger.error(f"Failed to write to clipboard after {self.max_retries} attempts: {e}")
                    return False
        
        return False
    
    def _set_image_to_clipboard(self, image: Image.Image) -> None:
        """
        Set image to Windows clipboard in DIB format.
        
        Args:
            image: PIL Image to copy to clipboard
        """
        # Convert image to BMP format in memory
        output = BytesIO()
        image.save(output, 'BMP')
        bmp_data = output.getvalue()
        
        # Skip BMP file header (14 bytes) to get DIB data
        dib_data = bmp_data[14:]
        
        # Set DIB data to clipboard
        win32clipboard.SetClipboardData(win32con.CF_DIB, dib_data)
