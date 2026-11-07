"""ClipboardItem model for representing clipboard entries."""

import hashlib
import os
from datetime import datetime
from typing import Optional, Dict, Any


class ClipboardItem:
    """Represents a single clipboard entry with content and metadata."""

    PREVIEW_LENGTH = 100

    def __init__(
        self,
        content_type: str,
        content: Optional[str] = None,
        image_path: Optional[str] = None,
        item_id: Optional[int] = None,
        timestamp: Optional[datetime] = None,
        pinned: bool = False
    ):
        """
        Initialize a ClipboardItem.

        Args:
            content_type: Type of content ('text', 'image', 'link')
            content: Text or link content
            image_path: Path to stored image file
            item_id: Unique identifier (set by storage layer)
            timestamp: When item was captured (defaults to now)
            pinned: Whether the item is pinned (kept at the top, never auto-deleted)
        """
        self.id = item_id
        self.content_type = content_type
        self.content = content
        self.image_path = image_path
        self.timestamp = timestamp or datetime.now()
        self.pinned = bool(pinned)
        # Size must be known before the preview is generated (image previews use it)
        self.size = self._calculate_size()
        self.preview = self._generate_preview()

    def _generate_preview(self) -> str:
        """Generate a preview string for display."""
        if self.content_type in ('text', 'link') and self.content:
            if len(self.content) > self.PREVIEW_LENGTH:
                return self.content[:self.PREVIEW_LENGTH] + '...'
            return self.content
        elif self.content_type == 'image':
            return f"Image ({self._format_size(self.size)})"
        return ""

    @staticmethod
    def _format_size(size: int) -> str:
        """Format a byte count as a short human readable string."""
        if size < 1024:
            return f"{size} B"
        if size < 1024 * 1024:
            return f"{size / 1024:.0f} KB"
        return f"{size / (1024 * 1024):.1f} MB"

    def _calculate_size(self) -> int:
        """Calculate content size in bytes."""
        if self.content:
            return len(self.content.encode('utf-8'))
        elif self.image_path and os.path.exists(self.image_path):
            return os.path.getsize(self.image_path)
        return 0

    def content_hash(self) -> str:
        """Stable hash of the content, used to detect duplicates in history."""
        if self.content_type in ('text', 'link') and self.content is not None:
            data = self.content.encode('utf-8')
        elif self.content_type == 'image' and self.image_path and os.path.exists(self.image_path):
            with open(self.image_path, 'rb') as f:
                data = f.read()
        else:
            return ""
        return hashlib.sha256(data).hexdigest()

    def is_link(self) -> bool:
        """Check if content is a URL."""
        if self.content_type == 'link':
            return True
        if self.content_type == 'text' and self.content:
            return self.content.strip().startswith(('http://', 'https://', 'ftp://'))
        return False

    def get_display_preview(self) -> str:
        """Return formatted preview text for display."""
        return self.preview

    def copy_to_clipboard(self) -> bool:
        """
        Copy this item to the system clipboard.

        Uses the Qt clipboard when a Qt application is running (works for text
        and images on every platform) and falls back to pyperclip for text.

        Returns:
            True if successful, False otherwise
        """
        try:
            if self.content_type in ('text', 'link') and self.content:
                return self._copy_text()
            if self.content_type == 'image' and self.image_path:
                return self._copy_image()
            return False
        except Exception:
            return False

    def _copy_text(self) -> bool:
        try:
            from PyQt5.QtWidgets import QApplication
            if QApplication.instance() is not None:
                QApplication.clipboard().setText(self.content)
                return True
        except ImportError:
            pass

        try:
            import pyperclip
            pyperclip.copy(self.content)
            return True
        except Exception:
            return False

    def _copy_image(self) -> bool:
        if not os.path.exists(self.image_path):
            return False
        try:
            from PyQt5.QtGui import QImage
            from PyQt5.QtWidgets import QApplication
        except ImportError:
            return False
        if QApplication.instance() is None:
            return False

        image = QImage(self.image_path)
        if image.isNull():
            return False
        QApplication.clipboard().setImage(image)
        return True

    def to_dict(self) -> Dict[str, Any]:
        """
        Serialize to dictionary.

        Returns:
            Dictionary representation of the clipboard item
        """
        return {
            'id': self.id,
            'content_type': self.content_type,
            'content': self.content,
            'image_path': self.image_path,
            'timestamp': self.timestamp.isoformat() if self.timestamp else None,
            'preview': self.preview,
            'size': self.size,
            'pinned': self.pinned
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'ClipboardItem':
        """
        Deserialize from dictionary.

        Args:
            data: Dictionary containing clipboard item data

        Returns:
            ClipboardItem instance
        """
        timestamp = None
        if data.get('timestamp'):
            timestamp = datetime.fromisoformat(data['timestamp'])

        return cls(
            content_type=data['content_type'],
            content=data.get('content'),
            image_path=data.get('image_path'),
            item_id=data.get('id'),
            timestamp=timestamp,
            pinned=bool(data.get('pinned', False))
        )

    def __repr__(self) -> str:
        """String representation for debugging."""
        return f"ClipboardItem(id={self.id}, type={self.content_type}, preview='{self.preview[:30]}...')"
