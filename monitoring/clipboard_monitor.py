"""Base ClipboardMonitor class for detecting clipboard changes."""

import threading
import time
import logging
from typing import Optional, Callable, Tuple, Any
from abc import ABC, abstractmethod


class ClipboardMonitor(ABC):
    """
    Abstract base class for clipboard monitoring.
    
    Monitors system clipboard for changes and triggers callbacks when new content is detected.
    Platform-specific implementations should inherit from this class.
    """
    
    def __init__(self, poll_interval: float = 0.5):
        """
        Initialize the clipboard monitor.
        
        Args:
            poll_interval: Time in seconds between clipboard checks (default 0.5s)
        """
        self.logger = logging.getLogger(self.__class__.__name__)
        self.poll_interval = poll_interval
        self._monitoring = False
        self._monitor_thread: Optional[threading.Thread] = None
        self._last_content: Optional[str] = None
        self._last_content_hash: Optional[int] = None
        self._callback: Optional[Callable[[str, str], None]] = None
        self._lock = threading.Lock()
    
    def start_monitoring(self) -> bool:
        """
        Start monitoring the clipboard in a background thread.
        
        Returns:
            True if monitoring started successfully, False otherwise
        """
        with self._lock:
            if self._monitoring:
                self.logger.warning("Clipboard monitoring is already running")
                return False
            
            self._monitoring = True
            self._monitor_thread = threading.Thread(
                target=self._monitor_loop,
                daemon=True,
                name="ClipboardMonitorThread"
            )
            self._monitor_thread.start()
            self.logger.info("Clipboard monitoring started")
            return True
    
    def stop_monitoring(self) -> bool:
        """
        Stop monitoring the clipboard.
        
        Returns:
            True if monitoring stopped successfully, False otherwise
        """
        with self._lock:
            if not self._monitoring:
                self.logger.warning("Clipboard monitoring is not running")
                return False
            
            self._monitoring = False
        
        # Wait for thread to finish (with timeout)
        if self._monitor_thread and self._monitor_thread.is_alive():
            self._monitor_thread.join(timeout=2.0)
        
        self.logger.info("Clipboard monitoring stopped")
        return True
    
    def set_callback(self, callback: Callable[[str, str], None]) -> None:
        """
        Set the callback function to be called when clipboard changes.
        
        Args:
            callback: Function that takes (content, content_type) as arguments
        """
        self._callback = callback
        self.logger.debug("Clipboard change callback registered")
    
    def on_clipboard_change(self, content: Any, content_type: str) -> None:
        """
        Callback mechanism triggered when clipboard content changes.
        
        Args:
            content: The clipboard content (text string or image data)
            content_type: Type of content ('text', 'link', 'image')
        """
        if self._callback:
            try:
                self._callback(content, content_type)
            except Exception as e:
                self.logger.error(f"Error in clipboard change callback: {e}")
    
    @abstractmethod
    def get_clipboard_content(self) -> Tuple[Optional[Any], Optional[str]]:
        """
        Get current clipboard content and type.
        
        This method must be implemented by platform-specific subclasses.
        
        Returns:
            Tuple of (content, content_type) where:
            - content: The clipboard content (text string or image data)
            - content_type: 'text', 'link', 'image', or None if clipboard is empty
        """
        pass
    
    def _monitor_loop(self) -> None:
        """
        Main monitoring loop that runs in background thread.
        
        Continuously polls clipboard at specified interval and triggers
        callback when changes are detected.
        """
        self.logger.info("Clipboard monitor loop started")
        
        while self._monitoring:
            try:
                content, content_type = self.get_clipboard_content()
                
                if content is not None and content_type is not None:
                    # Check if content has changed
                    if self._has_content_changed(content, content_type):
                        self.logger.debug(f"Clipboard change detected: {content_type}")
                        self._update_last_content(content, content_type)
                        self.on_clipboard_change(content, content_type)
                
            except Exception as e:
                self.logger.error(f"Error in monitor loop: {e}")
            
            # Sleep for poll interval
            time.sleep(self.poll_interval)
        
        self.logger.info("Clipboard monitor loop stopped")
    
    def _has_content_changed(self, content: Any, content_type: str) -> bool:
        """
        Check if clipboard content has changed since last check.
        
        Args:
            content: Current clipboard content
            content_type: Type of content
            
        Returns:
            True if content has changed, False otherwise
        """
        # For text/link content, use hash comparison for efficiency
        if content_type in ('text', 'link'):
            current_hash = hash(content)
            if current_hash != self._last_content_hash:
                return True
        # For images, always consider as changed if we got new image data
        elif content_type == 'image':
            # Image comparison is more complex, for now treat each capture as new
            return True
        
        return False
    
    def _update_last_content(self, content: Any, content_type: str) -> None:
        """
        Update the stored last content for change detection.
        
        Args:
            content: Current clipboard content
            content_type: Type of content
        """
        if content_type in ('text', 'link'):
            self._last_content = content
            self._last_content_hash = hash(content)
        elif content_type == 'image':
            # For images, we don't store the full content in memory
            self._last_content = None
            self._last_content_hash = None
    
    def is_monitoring(self) -> bool:
        """
        Check if monitoring is currently active.
        
        Returns:
            True if monitoring, False otherwise
        """
        return self._monitoring
    
    def __repr__(self) -> str:
        """String representation for debugging."""
        status = "running" if self._monitoring else "stopped"
        return f"{self.__class__.__name__}(status={status}, interval={self.poll_interval}s)"
