"""Storage Manager for persisting clipboard items using SQLite."""

import sqlite3
import os
import logging
from pathlib import Path
from typing import List, Optional
from datetime import datetime
import sys

# Add parent directory to path to import models
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from models.clipboard_item import ClipboardItem


class StorageManager:
    """Manages persistence of clipboard items using SQLite database."""
    
    def __init__(self, db_path: Optional[str] = None):
        """
        Initialize Storage Manager.
        
        Args:
            db_path: Path to database file (defaults to ~/.clipboard-manager/clipboard.db)
        """
        self.logger = logging.getLogger(self.__class__.__name__)
        
        if db_path is None:
            config_dir = Path.home() / '.clipboard-manager'
            config_dir.mkdir(parents=True, exist_ok=True)
            db_path = str(config_dir / 'clipboard.db')
        
        self.db_path = db_path
        self.logger.info(f"Initializing storage manager with database: {db_path}")
        self._init_database()
    
    def _init_database(self):
        """Initialize database schema and indexes."""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # Create clipboard_items table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS clipboard_items (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                content_type TEXT NOT NULL,
                content TEXT,
                image_path TEXT,
                timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
                preview TEXT,
                size INTEGER
            )
        ''')
        
        # Create indexes for performance
        cursor.execute('''
            CREATE INDEX IF NOT EXISTS idx_timestamp 
            ON clipboard_items(timestamp DESC)
        ''')
        
        cursor.execute('''
            CREATE INDEX IF NOT EXISTS idx_content_type 
            ON clipboard_items(content_type)
        ''')
        
        # Index for search optimization
        cursor.execute('''
            CREATE INDEX IF NOT EXISTS idx_content 
            ON clipboard_items(content)
        ''')
        
        cursor.execute('''
            CREATE INDEX IF NOT EXISTS idx_preview 
            ON clipboard_items(preview)
        ''')
        
        conn.commit()
        conn.close()
    
    def save_item(self, clipboard_item: ClipboardItem) -> bool:
        """
        Save a clipboard item to storage.
        
        Args:
            clipboard_item: ClipboardItem to persist
            
        Returns:
            True if successful, False otherwise
        """
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            cursor.execute('''
                INSERT INTO clipboard_items 
                (content_type, content, image_path, timestamp, preview, size)
                VALUES (?, ?, ?, ?, ?, ?)
            ''', (
                clipboard_item.content_type,
                clipboard_item.content,
                clipboard_item.image_path,
                clipboard_item.timestamp.isoformat(),
                clipboard_item.preview,
                clipboard_item.size
            ))
            
            clipboard_item.id = cursor.lastrowid
            conn.commit()
            conn.close()
            
            return True
        except sqlite3.Error as e:
            self.logger.error(f"Failed to save clipboard item: {e}")
            return False
    
    def get_all_items(self, limit: int = 1000) -> List[ClipboardItem]:
        """
        Retrieve all clipboard items with limit.
        
        Args:
            limit: Maximum number of items to retrieve (default 1000)
            
        Returns:
            List of ClipboardItem objects in reverse chronological order
        """
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            cursor.execute('''
                SELECT id, content_type, content, image_path, timestamp, preview, size
                FROM clipboard_items
                ORDER BY timestamp DESC
                LIMIT ?
            ''', (limit,))
            
            items = []
            for row in cursor.fetchall():
                item = ClipboardItem(
                    content_type=row[1],
                    content=row[2],
                    image_path=row[3],
                    item_id=row[0],
                    timestamp=datetime.fromisoformat(row[4])
                )
                items.append(item)
            
            conn.close()
            return items
        except sqlite3.Error as e:
            self.logger.error(f"Failed to retrieve clipboard items: {e}")
            return []
    
    def search_items(self, query: str, limit: int = 1000) -> List[ClipboardItem]:
        """
        Search clipboard items by text content.
        
        Args:
            query: Search query string
            limit: Maximum number of results (default 1000)
            
        Returns:
            List of matching ClipboardItem objects
        """
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            search_pattern = f'%{query}%'
            cursor.execute('''
                SELECT id, content_type, content, image_path, timestamp, preview, size
                FROM clipboard_items
                WHERE content LIKE ? OR preview LIKE ?
                ORDER BY timestamp DESC
                LIMIT ?
            ''', (search_pattern, search_pattern, limit))
            
            items = []
            for row in cursor.fetchall():
                item = ClipboardItem(
                    content_type=row[1],
                    content=row[2],
                    image_path=row[3],
                    item_id=row[0],
                    timestamp=datetime.fromisoformat(row[4])
                )
                items.append(item)
            
            conn.close()
            return items
        except sqlite3.Error as e:
            self.logger.error(f"Failed to search clipboard items: {e}")
            return []
    
    def delete_item(self, item_id: int) -> bool:
        """
        Delete a specific clipboard item.
        
        Args:
            item_id: ID of item to delete
            
        Returns:
            True if successful, False otherwise
        """
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            cursor.execute('DELETE FROM clipboard_items WHERE id = ?', (item_id,))
            
            conn.commit()
            conn.close()
            
            return True
        except sqlite3.Error as e:
            self.logger.error(f"Failed to delete clipboard item {item_id}: {e}")
            return False
    
    def clear_all_items(self) -> bool:
        """
        Delete all clipboard items.
        
        Returns:
            True if successful, False otherwise
        """
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            cursor.execute('DELETE FROM clipboard_items')
            
            conn.commit()
            conn.close()
            
            self.logger.info("All clipboard items cleared")
            return True
        except sqlite3.Error as e:
            self.logger.error(f"Failed to clear all clipboard items: {e}")
            return False
    
    def get_item_count(self) -> int:
        """
        Get total number of stored items.
        
        Returns:
            Count of clipboard items
        """
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            cursor.execute('SELECT COUNT(*) FROM clipboard_items')
            count = cursor.fetchone()[0]
            
            conn.close()
            return count
        except sqlite3.Error as e:
            self.logger.error(f"Failed to get item count: {e}")
            return 0
    
    def enforce_item_limit(self, max_items: int) -> bool:
        """
        Enforce maximum item limit by deleting oldest items.
        
        Args:
            max_items: Maximum number of items to keep
            
        Returns:
            True if successful, False otherwise
        """
        try:
            current_count = self.get_item_count()
            if current_count <= max_items:
                return True
            
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            # Delete oldest items beyond the limit
            cursor.execute('''
                DELETE FROM clipboard_items
                WHERE id IN (
                    SELECT id FROM clipboard_items
                    ORDER BY timestamp DESC
                    LIMIT -1 OFFSET ?
                )
            ''', (max_items,))
            
            conn.commit()
            conn.close()
            
            self.logger.info(f"Enforced storage limit: {max_items} items")
            return True
        except sqlite3.Error as e:
            self.logger.error(f"Failed to enforce item limit: {e}")
            return False
    
    def close(self):
        """Close database connection (cleanup method)."""
        # SQLite connections are opened and closed per operation
        # This method is here for API consistency
        pass
    
    def __repr__(self) -> str:
        """String representation for debugging."""
        return f"StorageManager(db_path={self.db_path}, items={self.get_item_count()})"
