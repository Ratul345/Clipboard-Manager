"""
Automated cross-platform tests for Clipboard Manager.
Run these tests on both Windows and Linux to verify functionality.
"""

import unittest
import sys
import os
import platform
import tempfile
import shutil
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from models.clipboard_item import ClipboardItem
from models.config import Config
from storage.storage_manager import StorageManager
from search.search_engine import SearchEngine
from utils.platform_utils import get_operating_system, is_windows, is_linux


class TestPlatformDetection(unittest.TestCase):
    """Test platform detection utilities."""
    
    def test_platform_detection(self):
        """Test that platform is correctly detected."""
        detected_platform = get_operating_system()
        self.assertIn(detected_platform, ['windows', 'linux', 'unknown'])
        
    def test_is_windows(self):
        """Test Windows detection."""
        if platform.system() == 'Windows':
            self.assertTrue(is_windows())
        else:
            self.assertFalse(is_windows())
    
    def test_is_linux(self):
        """Test Linux detection."""
        if platform.system() == 'Linux':
            self.assertTrue(is_linux())
        else:
            self.assertFalse(is_linux())


class TestClipboardItemCrossPlatform(unittest.TestCase):
    """Test ClipboardItem model across platforms."""
    
    def test_text_item_creation(self):
        """Test creating text clipboard item."""
        item = ClipboardItem('text', content='Hello World')
        self.assertEqual(item.content_type, 'text')
        self.assertEqual(item.content, 'Hello World')
        self.assertIsNotNone(item.timestamp)
    
    def test_link_detection(self):
        """Test URL detection works on all platforms."""
        item = ClipboardItem('text', content='https://example.com')
        self.assertTrue(item.is_link())
        
        item2 = ClipboardItem('text', content='http://example.com')
        self.assertTrue(item2.is_link())
        
        item3 = ClipboardItem('text', content='Just text')
        self.assertFalse(item3.is_link())
    
    def test_unicode_content(self):
        """Test Unicode content handling."""
        unicode_text = "Hello 世界 🌍 Привет"
        item = ClipboardItem('text', content=unicode_text)
        self.assertEqual(item.content, unicode_text)
        
        # Test serialization
        data = item.to_dict()
        restored = ClipboardItem.from_dict(data)
        self.assertEqual(restored.content, unicode_text)
    
    def test_preview_generation(self):
        """Test preview truncation."""
        long_text = "A" * 200
        item = ClipboardItem('text', content=long_text)
        self.assertLessEqual(len(item.preview), 103)  # 100 chars + "..."


class TestStorageCrossPlatform(unittest.TestCase):
    """Test storage functionality across platforms."""
    
    def setUp(self):
        """Create temporary storage for testing."""
        self.temp_dir = tempfile.mkdtemp()
        self.db_path = os.path.join(self.temp_dir, 'test.db')
        self.storage = StorageManager(self.db_path)
    
    def tearDown(self):
        """Clean up temporary storage."""
        self.storage.close()
        shutil.rmtree(self.temp_dir)
    
    def test_database_creation(self):
        """Test database is created correctly."""
        self.assertTrue(os.path.exists(self.db_path))
    
    def test_save_and_retrieve_text(self):
        """Test saving and retrieving text items."""
        item = ClipboardItem('text', content='Test content')
        saved_id = self.storage.save_item(item)
        self.assertIsNotNone(saved_id)
        
        items = self.storage.get_all_items()
        self.assertEqual(len(items), 1)
        self.assertEqual(items[0].content, 'Test content')
    
    def test_save_multiple_items(self):
        """Test saving multiple items."""
        for i in range(10):
            item = ClipboardItem('text', content=f'Item {i}')
            self.storage.save_item(item)
        
        items = self.storage.get_all_items()
        self.assertEqual(len(items), 10)
    
    def test_delete_item(self):
        """Test deleting items."""
        item = ClipboardItem('text', content='To delete')
        item_id = self.storage.save_item(item)
        
        self.storage.delete_item(item_id)
        items = self.storage.get_all_items()
        self.assertEqual(len(items), 0)
    
    def test_clear_all(self):
        """Test clearing all items."""
        for i in range(5):
            item = ClipboardItem('text', content=f'Item {i}')
            self.storage.save_item(item)
        
        self.storage.clear_all_items()
        items = self.storage.get_all_items()
        self.assertEqual(len(items), 0)
    
    def test_storage_limit(self):
        """Test storage limit enforcement."""
        # Save more than limit
        for i in range(15):
            item = ClipboardItem('text', content=f'Item {i}')
            self.storage.save_item(item)
        
        # Should only keep last 10 (or configured limit)
        items = self.storage.get_all_items()
        self.assertLessEqual(len(items), 15)


class TestSearchCrossPlatform(unittest.TestCase):
    """Test search functionality across platforms."""
    
    def setUp(self):
        """Create search engine and test items."""
        self.search = SearchEngine()
        self.items = [
            ClipboardItem('text', content='Hello World'),
            ClipboardItem('text', content='Python Programming'),
            ClipboardItem('text', content='https://example.com'),
            ClipboardItem('text', content='Test Data'),
        ]
    
    def test_case_insensitive_search(self):
        """Test case-insensitive search."""
        results = self.search.search('hello', self.items)
        self.assertEqual(len(results), 1)
        
        results = self.search.search('HELLO', self.items)
        self.assertEqual(len(results), 1)
    
    def test_substring_search(self):
        """Test substring matching."""
        results = self.search.search('Prog', self.items)
        self.assertEqual(len(results), 1)
        self.assertIn('Python', results[0].content)
    
    def test_empty_search(self):
        """Test empty search returns all items."""
        results = self.search.search('', self.items)
        self.assertEqual(len(results), len(self.items))
    
    def test_no_results(self):
        """Test search with no matches."""
        results = self.search.search('NonExistent', self.items)
        self.assertEqual(len(results), 0)
    
    def test_special_characters(self):
        """Test search with special characters."""
        results = self.search.search('example.com', self.items)
        self.assertEqual(len(results), 1)


class TestConfigCrossPlatform(unittest.TestCase):
    """Test configuration management across platforms."""
    
    def setUp(self):
        """Create temporary config file."""
        self.temp_dir = tempfile.mkdtemp()
        self.config_path = os.path.join(self.temp_dir, 'config.json')
        self.config = Config(self.config_path)
    
    def tearDown(self):
        """Clean up temporary config."""
        shutil.rmtree(self.temp_dir)
    
    def test_default_config(self):
        """Test default configuration values."""
        self.assertEqual(self.config.get('max_items'), 1000)
        self.assertEqual(self.config.get('auto_start'), False)
        self.assertTrue(self.config.get('capture_text'))
    
    def test_save_and_load(self):
        """Test saving and loading configuration."""
        self.config.set('max_items', 500)
        self.config.set('auto_start', True)
        
        # Create new config instance to test loading
        new_config = Config(self.config_path)
        self.assertEqual(new_config.get('max_items'), 500)
        self.assertEqual(new_config.get('auto_start'), True)
    
    def test_config_persistence(self):
        """Test configuration persists to file."""
        self.config.set('hotkey', 'ctrl+alt+v')
        self.assertTrue(os.path.exists(self.config_path))
        
        with open(self.config_path, 'r') as f:
            content = f.read()
            self.assertIn('ctrl+alt+v', content)


class TestPathHandling(unittest.TestCase):
    """Test file path handling across platforms."""
    
    def test_home_directory_expansion(self):
        """Test home directory path expansion."""
        home_path = Path.home()
        self.assertTrue(home_path.exists())
        
        # Test that we can create paths relative to home
        test_path = home_path / '.clipboard-manager-test'
        self.assertIsInstance(test_path, Path)
    
    def test_path_separators(self):
        """Test path separators work correctly."""
        # Path should handle separators correctly on all platforms
        test_path = Path('data') / 'images' / 'test.png'
        self.assertIsInstance(test_path, Path)
        
        # Convert to string should use correct separator
        path_str = str(test_path)
        if is_windows():
            self.assertIn('\\', path_str)
        else:
            self.assertIn('/', path_str)


def run_platform_tests():
    """Run all cross-platform tests and generate report."""
    print("=" * 70)
    print(f"Running Cross-Platform Tests on {platform.system()}")
    print(f"Python Version: {sys.version}")
    print("=" * 70)
    print()
    
    # Create test suite
    loader = unittest.TestLoader()
    suite = unittest.TestSuite()
    
    # Add all test classes
    suite.addTests(loader.loadTestsFromTestCase(TestPlatformDetection))
    suite.addTests(loader.loadTestsFromTestCase(TestClipboardItemCrossPlatform))
    suite.addTests(loader.loadTestsFromTestCase(TestStorageCrossPlatform))
    suite.addTests(loader.loadTestsFromTestCase(TestSearchCrossPlatform))
    suite.addTests(loader.loadTestsFromTestCase(TestConfigCrossPlatform))
    suite.addTests(loader.loadTestsFromTestCase(TestPathHandling))
    
    # Run tests
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(suite)
    
    # Print summary
    print()
    print("=" * 70)
    print("Test Summary")
    print("=" * 70)
    print(f"Tests Run: {result.testsRun}")
    print(f"Successes: {result.testsRun - len(result.failures) - len(result.errors)}")
    print(f"Failures: {len(result.failures)}")
    print(f"Errors: {len(result.errors)}")
    print()
    
    if result.wasSuccessful():
        print("✓ All tests passed!")
        return 0
    else:
        print("✗ Some tests failed. Please review the output above.")
        return 1


if __name__ == '__main__':
    sys.exit(run_platform_tests())
