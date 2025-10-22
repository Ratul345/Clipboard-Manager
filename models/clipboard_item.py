"""ClipboardItem model for representing clipboard entries."""

import os
from datetime import datetime
from typing import Optional, Dict, Any
import pyperclip


class ClipboardItem:
    """Represents a single clipboard entry with content and metadata."""
    
    def __init__(
        self,
        content_type: str,
        content: Optional[str] = None,
        image_path: Optional[str] = None,
        item_id: Optional[int] = None,
        timestamp: Optional[datetime] = None
    ):
        """
        Initialize a ClipboardItem.
        
        Args:
            content_type: Type of content ('text', 'image', 'link')
            content: Text or link content
            image_path: Path to stored image file
            item_id: Unique identifier (set by storage layer)
            timestamp: When item was captured (defaults to now)
        """
        self.id = item_id
        self.content_type = content_type
        self.content = content
        self.image_path = image_path
        self.timestamp = timestamp or datetime.now()
        self.preview = self._generate_preview()
        self.size = self._calculate_size()
    
    def _generate_preview(self) -> str:
        """Generate a preview string for display (max 100 characters)."""
        if self.content_type in ('text', 'link') and self.content:
            if len(self.content) > 100:
                return self.content[:100] + '...'
            return self.content
        elif self.content_type == 'image':
            return f"Image ({self.size} bytes)"
        return ""
    
    def _calculate_size(self) -> int:
        """Calculate content size in bytes."""
        if self.content:
            return len(self.content.encode('utf-8'))
        elif self.image_path and os.path.exists(self.image_path):
            return os.path.getsize(self.image_path)
        return 0
    
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
        
        Returns:
            True if successful, False otherwise
        """
        try:
            if self.content_type in ('text', 'link') and self.content:
                pyperclip.copy(self.content)
                return True
            elif self.content_type == 'image' and self.image_path:
                # Image copying will be handled by platform-specific clipboard monitor
                # For now, we just return False as this requires platform-specific code
                return False
            return False
        except Exception:
            return False
    
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
            'size': self.size
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
            timestamp=timestamp
        )
    
    def __repr__(self) -> str:
        """String representation for debugging."""
        return f"ClipboardItem(id={self.id}, type={self.content_type}, preview='{self.preview[:30]}...')"
