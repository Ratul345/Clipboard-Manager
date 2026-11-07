"""
Unit tests for the non-GUI core of Clipboard Manager.

Covers regressions for: image items, duplicate handling, pinning, storage
limits, link detection and HTML-safe search highlighting.
Run with:  python -m unittest tests.test_core -v
"""

import os
import shutil
import sys
import tempfile
import unittest
from datetime import datetime, timedelta

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from PIL import Image

from models.clipboard_item import ClipboardItem
from monitoring.clipboard_service import ClipboardService
from search.search_engine import SearchEngine
from storage.image_storage import ImageStorage
from storage.storage_manager import StorageManager


class CoreTestCase(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.mkdtemp()
        self.storage = StorageManager(os.path.join(self.tmp, 'test.db'))
        self.images = ImageStorage(os.path.join(self.tmp, 'images'))

    def tearDown(self):
        shutil.rmtree(self.tmp, ignore_errors=True)

    def make_service(self, max_items=1000):
        service = ClipboardService(self.storage, self.images, max_items=max_items)
        service.monitor = None  # no real clipboard in tests
        return service


class TestClipboardItem(CoreTestCase):
    def test_image_item_can_be_created(self):
        # Used to raise AttributeError because the preview was built before size existed
        path = self.images.save_image(Image.new('RGB', (4, 4), 'red'))
        item = ClipboardItem('image', image_path=path)
        self.assertTrue(item.preview.startswith('Image ('))
        self.assertGreater(item.size, 0)

    def test_pinned_roundtrip(self):
        item = ClipboardItem('text', content='hello', pinned=True)
        restored = ClipboardItem.from_dict(item.to_dict())
        self.assertTrue(restored.pinned)

    def test_content_hash_matches_for_equal_text(self):
        self.assertEqual(
            ClipboardItem('text', content='a').content_hash(),
            ClipboardItem('text', content='a').content_hash(),
        )


class TestImageStorage(CoreTestCase):
    def test_saves_pil_image(self):
        path = self.images.save_image(Image.new('RGBA', (8, 8), (0, 0, 255, 128)))
        self.assertIsNotNone(path)
        self.assertTrue(os.path.exists(path))

    def test_saves_raw_bytes(self):
        import io
        buffer = io.BytesIO()
        Image.new('RGB', (4, 4)).save(buffer, 'PNG')
        self.assertIsNotNone(self.images.save_image(buffer.getvalue()))


class TestStorage(CoreTestCase):
    def test_pinned_items_sort_first(self):
        old = ClipboardItem('text', content='old', timestamp=datetime.now() - timedelta(days=1))
        new = ClipboardItem('text', content='new')
        self.storage.save_item(old)
        self.storage.save_item(new)
        self.storage.set_pinned(old.id, True)
        contents = [i.content for i in self.storage.get_all_items()]
        self.assertEqual(contents, ['old', 'new'])

    def test_touch_moves_item_to_top(self):
        first = ClipboardItem('text', content='first', timestamp=datetime.now() - timedelta(hours=2))
        second = ClipboardItem('text', content='second', timestamp=datetime.now() - timedelta(hours=1))
        self.storage.save_item(first)
        self.storage.save_item(second)
        self.storage.touch_item(first.id)
        self.assertEqual(self.storage.get_all_items()[0].content, 'first')

    def test_limit_never_deletes_pinned(self):
        items = []
        for i in range(5):
            item = ClipboardItem('text', content=f'item {i}',
                                 timestamp=datetime.now() - timedelta(minutes=10 - i))
            self.storage.save_item(item)
            items.append(item)
        self.storage.set_pinned(items[0].id, True)  # the oldest one
        self.storage.enforce_item_limit(2)
        remaining = {i.content for i in self.storage.get_all_items()}
        self.assertIn('item 0', remaining)       # pinned survives
        self.assertEqual(len(remaining), 3)      # pinned + 2 newest unpinned

    def test_delete_removes_image_file(self):
        path = self.images.save_image(Image.new('RGB', (4, 4)))
        item = ClipboardItem('image', image_path=path)
        self.storage.save_item(item)
        self.storage.delete_item(item.id)
        self.assertFalse(os.path.exists(path))

    def test_clear_all_can_keep_pinned(self):
        keep = ClipboardItem('text', content='keep')
        drop = ClipboardItem('text', content='drop')
        self.storage.save_item(keep)
        self.storage.save_item(drop)
        self.storage.set_pinned(keep.id, True)
        self.storage.clear_all_items(keep_pinned=True)
        self.assertEqual([i.content for i in self.storage.get_all_items()], ['keep'])
        self.storage.clear_all_items()
        self.assertEqual(self.storage.get_item_count(), 0)

    def test_search_treats_wildcards_literally(self):
        self.storage.save_item(ClipboardItem('text', content='100% sure'))
        self.storage.save_item(ClipboardItem('text', content='plain'))
        self.assertEqual(len(self.storage.search_items('%')), 1)

    def test_old_database_is_migrated(self):
        import sqlite3
        db = os.path.join(self.tmp, 'old.db')
        conn = sqlite3.connect(db)
        conn.execute('''CREATE TABLE clipboard_items (
            id INTEGER PRIMARY KEY AUTOINCREMENT, content_type TEXT NOT NULL, content TEXT,
            image_path TEXT, timestamp DATETIME DEFAULT CURRENT_TIMESTAMP, preview TEXT, size INTEGER)''')
        conn.execute("INSERT INTO clipboard_items (content_type, content, timestamp) "
                     "VALUES ('text', 'legacy', ?)", (datetime.now().isoformat(),))
        conn.commit()
        conn.close()
        migrated = StorageManager(db)
        items = migrated.get_all_items()
        self.assertEqual(items[0].content, 'legacy')
        self.assertFalse(items[0].pinned)


class TestService(CoreTestCase):
    def test_recopying_existing_text_does_not_duplicate(self):
        service = self.make_service()
        service._on_clipboard_change('alpha', 'text')
        service._on_clipboard_change('beta', 'text')
        service._on_clipboard_change('alpha', 'text')   # picked again from history
        contents = [i.content for i in self.storage.get_all_items()]
        self.assertEqual(sorted(contents), ['alpha', 'beta'])
        self.assertEqual(contents[0], 'alpha')           # and it moved to the top

    def test_image_is_captured_and_deduplicated(self):
        service = self.make_service()
        service._on_clipboard_change(Image.new('RGB', (6, 6), 'green'), 'image')
        service._on_clipboard_change(Image.new('RGB', (2, 2), 'blue'), 'image')
        service._on_clipboard_change(Image.new('RGB', (6, 6), 'green'), 'image')
        self.assertEqual(self.storage.get_item_count(), 2)

    def test_added_callback_fires(self):
        service = self.make_service()
        seen = []
        service.set_item_added_callback(seen.append)
        service._on_clipboard_change('hello', 'text')
        self.assertEqual(len(seen), 1)

    def test_link_detection(self):
        looks = ClipboardService.looks_like_link
        self.assertTrue(looks('https://example.com/a?b=1'))
        self.assertTrue(looks('www.example.com'))
        self.assertFalse(looks('main.py'))
        self.assertFalse(looks('3.14'))
        self.assertFalse(looks('see https://example.com for details'))
        self.assertFalse(looks('first line\nhttps://example.com'))

    def test_pinned_items_survive_service_limit(self):
        service = self.make_service(max_items=2)
        service._on_clipboard_change('one', 'text')
        pinned_id = self.storage.get_all_items()[0].id
        self.storage.set_pinned(pinned_id, True)
        for text in ('two', 'three', 'four'):
            service._on_clipboard_change(text, 'text')
        contents = {i.content for i in self.storage.get_all_items()}
        self.assertIn('one', contents)
        self.assertEqual(len(contents), 3)


class TestSearch(unittest.TestCase):
    def setUp(self):
        self.engine = SearchEngine()

    def test_highlight_html_escapes_clipboard_content(self):
        result = self.engine.highlight_html('<b>bold</b> text', 'text')
        self.assertNotIn('<b>', result)
        self.assertIn('&lt;b&gt;', result)
        self.assertIn('<mark>text</mark>', result)

    def test_highlight_html_without_query_still_escapes(self):
        self.assertEqual(self.engine.highlight_html('a < b', ''), 'a &lt; b')

    def test_highlight_is_case_insensitive_and_keeps_original_case(self):
        self.assertEqual(self.engine.highlight_html('Hello', 'hello'), '<mark>Hello</mark>')

    def test_search_filters_items(self):
        items = [ClipboardItem('text', content='Python'), ClipboardItem('text', content='Rust')]
        self.assertEqual(len(self.engine.search('pyth', items)), 1)


if __name__ == '__main__':
    unittest.main()
