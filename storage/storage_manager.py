"""Storage Manager for persisting clipboard items using SQLite."""

import sqlite3
import os
import logging
from contextlib import contextmanager
from pathlib import Path
from typing import Iterator, List, Optional
from datetime import datetime
import sys

# Add parent directory to path to import models
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from models.clipboard_item import ClipboardItem


_COLUMNS = "id, content_type, content, image_path, timestamp, pinned"


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

    @contextmanager
    def _connect(self) -> Iterator[sqlite3.Connection]:
        """Open a connection that is always committed/rolled back and closed.

        The monitor thread and the UI thread both use the database, so every
        operation gets its own short-lived connection with a busy timeout.
        """
        conn = sqlite3.connect(self.db_path, timeout=10)
        try:
            yield conn
            conn.commit()
        except Exception:
            conn.rollback()
            raise
        finally:
            conn.close()

    def _init_database(self):
        """Initialize database schema, indexes and migrations."""
        with self._connect() as conn:
            cursor = conn.cursor()

            cursor.execute('''
                CREATE TABLE IF NOT EXISTS clipboard_items (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    content_type TEXT NOT NULL,
                    content TEXT,
                    image_path TEXT,
                    timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
                    preview TEXT,
                    size INTEGER,
                    pinned INTEGER NOT NULL DEFAULT 0
                )
            ''')

            # Migration: databases created before pinning existed lack the column
            columns = [row[1] for row in cursor.execute('PRAGMA table_info(clipboard_items)')]
            if 'pinned' not in columns:
                cursor.execute(
                    'ALTER TABLE clipboard_items ADD COLUMN pinned INTEGER NOT NULL DEFAULT 0'
                )

            cursor.execute('''
                CREATE INDEX IF NOT EXISTS idx_timestamp
                ON clipboard_items(timestamp DESC)
            ''')
            cursor.execute('''
                CREATE INDEX IF NOT EXISTS idx_content_type
                ON clipboard_items(content_type)
            ''')

    @staticmethod
    def _row_to_item(row) -> ClipboardItem:
        return ClipboardItem(
            content_type=row[1],
            content=row[2],
            image_path=row[3],
            item_id=row[0],
            timestamp=datetime.fromisoformat(row[4]),
            pinned=bool(row[5])
        )

    def save_item(self, clipboard_item: ClipboardItem) -> bool:
        """
        Save a clipboard item to storage.

        Args:
            clipboard_item: ClipboardItem to persist

        Returns:
            True if successful, False otherwise
        """
        try:
            with self._connect() as conn:
                cursor = conn.cursor()
                cursor.execute('''
                    INSERT INTO clipboard_items
                    (content_type, content, image_path, timestamp, preview, size, pinned)
                    VALUES (?, ?, ?, ?, ?, ?, ?)
                ''', (
                    clipboard_item.content_type,
                    clipboard_item.content,
                    clipboard_item.image_path,
                    clipboard_item.timestamp.isoformat(),
                    clipboard_item.preview,
                    clipboard_item.size,
                    1 if clipboard_item.pinned else 0
                ))
                clipboard_item.id = cursor.lastrowid
            return True
        except sqlite3.Error as e:
            self.logger.error(f"Failed to save clipboard item: {e}")
            return False

    def get_all_items(self, limit: int = 1000) -> List[ClipboardItem]:
        """
        Retrieve clipboard items, pinned first and then newest first.

        Args:
            limit: Maximum number of items to retrieve (default 1000)

        Returns:
            List of ClipboardItem objects
        """
        try:
            with self._connect() as conn:
                rows = conn.execute(f'''
                    SELECT {_COLUMNS}
                    FROM clipboard_items
                    ORDER BY pinned DESC, timestamp DESC, id DESC
                    LIMIT ?
                ''', (limit,)).fetchall()
            return [self._row_to_item(row) for row in rows]
        except sqlite3.Error as e:
            self.logger.error(f"Failed to retrieve clipboard items: {e}")
            return []

    def get_item(self, item_id: int) -> Optional[ClipboardItem]:
        """Return a single item by id, or None."""
        try:
            with self._connect() as conn:
                row = conn.execute(
                    f'SELECT {_COLUMNS} FROM clipboard_items WHERE id = ?', (item_id,)
                ).fetchone()
            return self._row_to_item(row) if row else None
        except sqlite3.Error as e:
            self.logger.error(f"Failed to load clipboard item {item_id}: {e}")
            return None

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
            escaped = query.replace('\\', '\\\\').replace('%', '\\%').replace('_', '\\_')
            pattern = f'%{escaped}%'
            with self._connect() as conn:
                rows = conn.execute(f'''
                    SELECT {_COLUMNS}
                    FROM clipboard_items
                    WHERE content LIKE ? ESCAPE '\\' OR preview LIKE ? ESCAPE '\\'
                    ORDER BY pinned DESC, timestamp DESC, id DESC
                    LIMIT ?
                ''', (pattern, pattern, limit)).fetchall()
            return [self._row_to_item(row) for row in rows]
        except sqlite3.Error as e:
            self.logger.error(f"Failed to search clipboard items: {e}")
            return []

    def find_by_content(self, content_type: str, content: str) -> Optional[ClipboardItem]:
        """Find an existing text/link item with exactly this content."""
        try:
            with self._connect() as conn:
                row = conn.execute(f'''
                    SELECT {_COLUMNS} FROM clipboard_items
                    WHERE content_type = ? AND content = ?
                    ORDER BY id DESC LIMIT 1
                ''', (content_type, content)).fetchone()
            return self._row_to_item(row) if row else None
        except sqlite3.Error as e:
            self.logger.error(f"Failed to look up clipboard item: {e}")
            return None

    def find_image_by_hash(self, content_hash: str, recent: int = 50) -> Optional[ClipboardItem]:
        """Find a recently stored image whose file content matches the given hash."""
        try:
            with self._connect() as conn:
                rows = conn.execute(f'''
                    SELECT {_COLUMNS} FROM clipboard_items
                    WHERE content_type = 'image'
                    ORDER BY id DESC
                    LIMIT ?
                ''', (recent,)).fetchall()
        except sqlite3.Error as e:
            self.logger.error(f"Failed to look up image items: {e}")
            return None

        for row in rows:
            item = self._row_to_item(row)
            if item.content_hash() == content_hash:
                return item
        return None

    def touch_item(self, item_id: int) -> bool:
        """Mark an item as used just now so it moves to the top of the history."""
        try:
            with self._connect() as conn:
                conn.execute(
                    'UPDATE clipboard_items SET timestamp = ? WHERE id = ?',
                    (datetime.now().isoformat(), item_id)
                )
            return True
        except sqlite3.Error as e:
            self.logger.error(f"Failed to update clipboard item {item_id}: {e}")
            return False

    def set_pinned(self, item_id: int, pinned: bool) -> bool:
        """Pin or unpin an item."""
        try:
            with self._connect() as conn:
                conn.execute(
                    'UPDATE clipboard_items SET pinned = ? WHERE id = ?',
                    (1 if pinned else 0, item_id)
                )
            return True
        except sqlite3.Error as e:
            self.logger.error(f"Failed to update pin state for item {item_id}: {e}")
            return False

    @staticmethod
    def _remove_files(paths) -> None:
        """Delete image files that no longer have a database row."""
        for path in paths:
            if path:
                try:
                    os.remove(path)
                except OSError:
                    pass

    def delete_item(self, item_id: int) -> bool:
        """
        Delete a specific clipboard item (and its image file, if any).

        Args:
            item_id: ID of item to delete

        Returns:
            True if successful, False otherwise
        """
        try:
            with self._connect() as conn:
                row = conn.execute(
                    'SELECT image_path FROM clipboard_items WHERE id = ?', (item_id,)
                ).fetchone()
                conn.execute('DELETE FROM clipboard_items WHERE id = ?', (item_id,))
            if row:
                self._remove_files([row[0]])
            return True
        except sqlite3.Error as e:
            self.logger.error(f"Failed to delete clipboard item {item_id}: {e}")
            return False

    def clear_all_items(self, keep_pinned: bool = False) -> bool:
        """
        Delete clipboard items and their image files.

        Args:
            keep_pinned: When True, pinned items are left untouched

        Returns:
            True if successful, False otherwise
        """
        where = 'WHERE pinned = 0' if keep_pinned else ''
        try:
            with self._connect() as conn:
                paths = [r[0] for r in conn.execute(
                    f"SELECT image_path FROM clipboard_items {where} "
                    f"{'AND' if keep_pinned else 'WHERE'} image_path IS NOT NULL"
                )]
                conn.execute(f'DELETE FROM clipboard_items {where}')
            self._remove_files(paths)
            self.logger.info("Clipboard items cleared")
            return True
        except sqlite3.Error as e:
            self.logger.error(f"Failed to clear clipboard items: {e}")
            return False

    def get_item_count(self) -> int:
        """
        Get total number of stored items.

        Returns:
            Count of clipboard items
        """
        try:
            with self._connect() as conn:
                return conn.execute('SELECT COUNT(*) FROM clipboard_items').fetchone()[0]
        except sqlite3.Error as e:
            self.logger.error(f"Failed to get item count: {e}")
            return 0

    def enforce_item_limit(self, max_items: int) -> bool:
        """
        Enforce maximum item limit by deleting the oldest unpinned items.

        Pinned items are never deleted and do not count towards the limit.

        Args:
            max_items: Maximum number of unpinned items to keep

        Returns:
            True if successful, False otherwise
        """
        try:
            with self._connect() as conn:
                rows = conn.execute('''
                    SELECT id, image_path FROM clipboard_items
                    WHERE pinned = 0
                    ORDER BY timestamp DESC, id DESC
                    LIMIT -1 OFFSET ?
                ''', (max_items,)).fetchall()
                if not rows:
                    return True
                conn.executemany(
                    'DELETE FROM clipboard_items WHERE id = ?', [(r[0],) for r in rows]
                )
            self._remove_files([r[1] for r in rows])
            self.logger.info(f"Enforced storage limit: {max_items} items")
            return True
        except sqlite3.Error as e:
            self.logger.error(f"Failed to enforce item limit: {e}")
            return False

    def close(self):
        """Close database connection (cleanup method)."""
        # Connections are opened and closed per operation.
        # This method is here for API consistency.
        pass

    def __repr__(self) -> str:
        """String representation for debugging."""
        return f"StorageManager(db_path={self.db_path}, items={self.get_item_count()})"
