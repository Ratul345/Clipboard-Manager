"""SearchEngine for filtering and highlighting clipboard items."""

from typing import List, Tuple
import re
import sys
import os

# Add parent directory to path to import models
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from models.clipboard_item import ClipboardItem


class SearchEngine:
    """Handles searching and filtering of clipboard items."""
    
    def search(self, query: str, items: List[ClipboardItem]) -> List[ClipboardItem]:
        """
        Filter clipboard items based on search query.
        
        Performs case-insensitive substring matching on text content and link URLs.
        Images are filtered based on their preview text only.
        
        Args:
            query: Search query string
            items: List of ClipboardItem objects to search
            
        Returns:
            List of ClipboardItem objects that match the query
        """
        if not query or not query.strip():
            return items
        
        query_lower = query.lower()
        filtered_items = []
        
        for item in items:
            # Search in text content for text and link types
            if item.content_type in ('text', 'link') and item.content:
                if query_lower in item.content.lower():
                    filtered_items.append(item)
                    continue
            
            # Search in preview for all types (fallback)
            if item.preview and query_lower in item.preview.lower():
                filtered_items.append(item)
        
        return filtered_items
    
    def highlight_matches(self, text: str, query: str, 
                         start_tag: str = '<mark>', 
                         end_tag: str = '</mark>') -> str:
        """
        Mark matching text within a string with highlight tags.
        
        Performs case-insensitive matching and wraps all occurrences
        of the query string with the specified tags.
        
        Args:
            text: Text to search and highlight
            query: Search query to highlight
            start_tag: Opening tag for highlighting (default: '<mark>')
            end_tag: Closing tag for highlighting (default: '</mark>')
            
        Returns:
            Text with matching portions wrapped in highlight tags
        """
        if not query or not query.strip() or not text:
            return text
        
        # Escape special regex characters in query
        escaped_query = re.escape(query)
        
        # Create case-insensitive regex pattern
        pattern = re.compile(f'({escaped_query})', re.IGNORECASE)
        
        # Replace all matches with highlighted version
        highlighted = pattern.sub(f'{start_tag}\\1{end_tag}', text)
        
        return highlighted
    
    def get_match_positions(self, text: str, query: str) -> List[Tuple[int, int]]:
        """
        Get positions of all matches in text.
        
        Useful for UI highlighting without modifying the original text.
        
        Args:
            text: Text to search
            query: Search query
            
        Returns:
            List of (start, end) tuples indicating match positions
        """
        if not query or not query.strip() or not text:
            return []
        
        positions = []
        query_lower = query.lower()
        text_lower = text.lower()
        query_len = len(query)
        
        start = 0
        while True:
            pos = text_lower.find(query_lower, start)
            if pos == -1:
                break
            positions.append((pos, pos + query_len))
            start = pos + 1
        
        return positions
    
    def __repr__(self) -> str:
        """String representation for debugging."""
        return "SearchEngine()"
