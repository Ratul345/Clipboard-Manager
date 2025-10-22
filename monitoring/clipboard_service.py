"""Clipboard service that integrates monitoring with storage."""

import logging
import hashlib
from typing import Optional
from pathlib import Path
from datetime import datetime

try:
    from PIL import Image
    PIL_AVAILABLE = True
except ImportError:
    PIL_AVAILABLE = False

from models.clipboard_item import ClipboardItem
from storage.storage_manager import StorageManager
from storage.image_storage import ImageStorage
from utils.platform_utils import is_windows, is_linux


class ClipboardService:
    """
    Service that coordinates clipboard monitoring with storage.
    
    Handles duplicate detection, content type classification, and storage limit enforcement.
    """
    
    def __init__(
        self,
        storage_manager: StorageManager,
        image_storage: ImageStorage,
        max_items: int = 1000,
        capture_text: bool = True,
        capture_images: bool = True,
        capture_links: bool = True
    ):
        """
        Initialize clipboard service.
        
        Args:
            storage_manager: Storage manager for persisting items
            image_storage: Image storage for saving image files
            max_items: Maximum number of items to store (default 1000)
            capture_text: Whether to capture text content (default True)
            capture_images: Whether to capture images (default True)
            capture_links: Whether to capture links (default True)
        """
        self.logger = logging.getLogger(self.__class__.__name__)
        self.storage_manager = storage_manager
        self.image_storage = image_storage
        self.max_items = max_items
        self.monitor: Optional[object] = None
        self._last_content_hash: Optional[str] = None
        
        # Capture filters
        self.capture_text = capture_text
        self.capture_images = capture_images
        self.capture_links = capture_links
        
        # Initialize platform-specific monitor
        self._init_monitor()
    
    def _init_monitor(self) -> None:
        """Initialize the appropriate clipboard monitor for the current platform."""
        try:
            if is_windows():
                from monitoring.windows_monitor import WindowsClipboardMonitor
                self.monitor = WindowsClipboardMonitor()
                self.logger.info("Initialized Windows clipboard monitor")
            elif is_linux():
                from monitoring.linux_monitor import LinuxClipboardMonitor
                self.monitor = LinuxClipboardMonitor()
                self.logger.info("Initialized Linux clipboard monitor")
            else:
                self.logger.error("Unsupported platform for clipboard monitoring")
                self.monitor = None
        except Exception as e:
            self.logger.error(f"Failed to initialize clipboard monitor: {e}")
            self.monitor = None
    
    def start(self) -> bool:
        """
        Start clipboard monitoring.
        
        Returns:
            True if monitoring started successfully, False otherwise
        """
        if not self.monitor:
            self.logger.error("Clipboard monitor not initialized")
            return False
        
        # Set callback for clipboard changes
        self.monitor.set_callback(self._on_clipboard_change)
        
        # Start monitoring
        success = self.monitor.start_monitoring()
        
        if success:
            self.logger.info("Clipboard monitoring started")
        else:
            self.logger.error("Failed to start clipboard monitoring")
        
        return success
    
    def stop(self) -> bool:
        """
        Stop clipboard monitoring.
        
        Returns:
            True if monitoring stopped successfully, False otherwise
        """
        if not self.monitor:
            return False
        
        success = self.monitor.stop_monitoring()
        
        if success:
            self.logger.info("Clipboard monitoring stopped")
        else:
            self.logger.error("Failed to stop clipboard monitoring")
        
        return success
    
    def _on_clipboard_change(self, content, content_type: str) -> None:
        """
        Callback triggered when clipboard content changes.
        
        Args:
            content: Clipboard content (text string or PIL Image)
            content_type: Type of content ('text', 'link', 'image')
        """
        try:
            # Check for duplicates
            if self._is_duplicate(content, content_type):
                self.logger.debug("Duplicate content detected, skipping")
                return
            
            # Detect and refine content type
            refined_type = self._detect_content_type(content, content_type)
            
            # Check if this content type should be captured
            if not self._should_capture(refined_type):
                self.logger.debug(f"Content type {refined_type} is disabled, skipping")
                return
            
            # Create clipboard item
            clipboard_item = self._create_clipboard_item(content, refined_type)
            
            if not clipboard_item:
                self.logger.warning("Failed to create clipboard item")
                return
            
            # Save to storage
            if self.storage_manager.save_item(clipboard_item):
                self.logger.info(f"Saved clipboard item: {refined_type}")
                
                # Enforce storage limit
                self._enforce_storage_limit()
            else:
                self.logger.error("Failed to save clipboard item")
        
        except Exception as e:
            self.logger.error(f"Error processing clipboard change: {e}")
    
    def _is_duplicate(self, content, content_type: str) -> bool:
        """
        Check if content is a duplicate of the last captured item.
        
        Args:
            content: Clipboard content
            content_type: Type of content
            
        Returns:
            True if duplicate, False otherwise
        """
        try:
            # Generate hash of content
            content_hash = self._generate_content_hash(content, content_type)
            
            # Compare with last hash
            if content_hash == self._last_content_hash:
                return True
            
            # Update last hash
            self._last_content_hash = content_hash
            return False
        
        except Exception as e:
            self.logger.error(f"Error checking for duplicates: {e}")
            return False
    
    def _generate_content_hash(self, content, content_type: str) -> str:
        """
        Generate a hash of the content for duplicate detection.
        
        Args:
            content: Clipboard content
            content_type: Type of content
            
        Returns:
            Hash string
        """
        if content_type in ('text', 'link'):
            # Hash text content
            return hashlib.sha256(content.encode('utf-8')).hexdigest()
        elif content_type == 'image' and PIL_AVAILABLE:
            # Hash image data
            if isinstance(content, Image.Image):
                # Convert image to bytes and hash
                import io
                buffer = io.BytesIO()
                content.save(buffer, format='PNG')
                return hashlib.sha256(buffer.getvalue()).hexdigest()
        
        return ""
    
    def _detect_content_type(self, content, initial_type: str) -> str:
        """
        Detect and refine content type.
        
        Args:
            content: Clipboard content
            initial_type: Initial content type from monitor
            
        Returns:
            Refined content type ('text', 'link', or 'image')
        """
        if initial_type == 'image':
            return 'image'
        
        if initial_type in ('text', 'link') and isinstance(content, str):
            # Check if it's a link
            content_stripped = content.strip()
            if content_stripped.startswith(('http://', 'https://', 'ftp://', 'ftps://')):
                return 'link'
            
            # Check if it looks like a URL without scheme
            if ('.' in content_stripped and 
                ' ' not in content_stripped and 
                '\n' not in content_stripped and
                len(content_stripped) < 500):
                # Simple heuristic for URLs
                if content_stripped.count('.') <= 10:
                    return 'link'
        
        return 'text'
    
    def _create_clipboard_item(self, content, content_type: str) -> Optional[ClipboardItem]:
        """
        Create a ClipboardItem from content.
        
        Args:
            content: Clipboard content
            content_type: Type of content
            
        Returns:
            ClipboardItem or None if creation fails
        """
        try:
            if content_type in ('text', 'link'):
                return ClipboardItem(
                    content_type=content_type,
                    content=content
                )
            
            elif content_type == 'image' and PIL_AVAILABLE:
                if isinstance(content, Image.Image):
                    # Save image to disk
                    image_path = self.image_storage.save_image(content)
                    
                    if image_path:
                        return ClipboardItem(
                            content_type='image',
                            image_path=image_path
                        )
                    else:
                        self.logger.error("Failed to save image to disk")
                        return None
            
            return None
        
        except Exception as e:
            self.logger.error(f"Error creating clipboard item: {e}")
            return None
    
    def _enforce_storage_limit(self) -> None:
        """Enforce maximum storage limit by deleting oldest items."""
        try:
            current_count = self.storage_manager.get_item_count()
            
            if current_count > self.max_items:
                self.logger.info(f"Storage limit exceeded ({current_count}/{self.max_items}), enforcing limit")
                self.storage_manager.enforce_item_limit(self.max_items)
        
        except Exception as e:
            self.logger.error(f"Error enforcing storage limit: {e}")
    
    def _should_capture(self, content_type: str) -> bool:
        """
        Check if content type should be captured based on settings.
        
        Args:
            content_type: Type of content ('text', 'link', 'image')
            
        Returns:
            True if should capture, False otherwise
        """
        if content_type == 'text':
            return self.capture_text
        elif content_type == 'link':
            return self.capture_links
        elif content_type == 'image':
            return self.capture_images
        return True
    
    def set_capture_settings(self, capture_text: bool = None, 
                            capture_images: bool = None, 
                            capture_links: bool = None) -> None:
        """
        Update capture settings.
        
        Args:
            capture_text: Whether to capture text (None to keep current)
            capture_images: Whether to capture images (None to keep current)
            capture_links: Whether to capture links (None to keep current)
        """
        if capture_text is not None:
            self.capture_text = capture_text
            self.logger.info(f"Capture text: {capture_text}")
        
        if capture_images is not None:
            self.capture_images = capture_images
            self.logger.info(f"Capture images: {capture_images}")
        
        if capture_links is not None:
            self.capture_links = capture_links
            self.logger.info(f"Capture links: {capture_links}")
    
    def set_max_items(self, max_items: int) -> None:
        """
        Update maximum items limit.
        
        Args:
            max_items: New maximum items limit
        """
        self.max_items = max_items
        self._enforce_storage_limit()
    
    def is_monitoring(self) -> bool:
        """
        Check if monitoring is currently active.
        
        Returns:
            True if monitoring, False otherwise
        """
        if self.monitor:
            return self.monitor.is_monitoring()
        return False
    
    def __repr__(self) -> str:
        """String representation for debugging."""
        status = "monitoring" if self.is_monitoring() else "stopped"
        return f"ClipboardService(status={status}, max_items={self.max_items})"
