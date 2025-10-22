"""Image storage functionality for clipboard images."""

import os
import shutil
from pathlib import Path
from typing import Optional
from datetime import datetime
from PIL import Image
import io


class ImageStorage:
    """Manages storage and retrieval of clipboard images."""
    
    def __init__(self, storage_dir: Optional[str] = None):
        """
        Initialize Image Storage.
        
        Args:
            storage_dir: Directory for image storage (defaults to ~/.clipboard-manager/images/)
        """
        if storage_dir is None:
            storage_dir = Path.home() / '.clipboard-manager' / 'images'
        
        self.storage_dir = Path(storage_dir)
        self._ensure_directory_exists()
    
    def _ensure_directory_exists(self):
        """Create storage directory if it doesn't exist."""
        self.storage_dir.mkdir(parents=True, exist_ok=True)
    
    def save_image(self, image_data: bytes, item_id: Optional[int] = None) -> Optional[str]:
        """
        Save image data to file with timestamp-based filename.
        
        Args:
            image_data: Raw image bytes
            item_id: Optional item ID to include in filename
            
        Returns:
            Path to saved image file, or None if failed
        """
        try:
            # Generate filename with timestamp
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S_%f')
            if item_id is not None:
                filename = f"{timestamp}_{item_id}.png"
            else:
                filename = f"{timestamp}.png"
            
            filepath = self.storage_dir / filename
            
            # Save image using PIL to ensure proper format
            image = Image.open(io.BytesIO(image_data))
            image.save(filepath, 'PNG')
            
            return str(filepath)
        except Exception:
            return None
    
    def save_image_from_path(self, source_path: str, item_id: Optional[int] = None) -> Optional[str]:
        """
        Copy image from source path to storage.
        
        Args:
            source_path: Path to source image file
            item_id: Optional item ID to include in filename
            
        Returns:
            Path to saved image file, or None if failed
        """
        try:
            if not os.path.exists(source_path):
                return None
            
            # Generate filename with timestamp
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S_%f')
            ext = os.path.splitext(source_path)[1] or '.png'
            
            if item_id is not None:
                filename = f"{timestamp}_{item_id}{ext}"
            else:
                filename = f"{timestamp}{ext}"
            
            filepath = self.storage_dir / filename
            
            # Copy and convert to PNG for consistency
            image = Image.open(source_path)
            image.save(filepath, 'PNG')
            
            return str(filepath)
        except Exception:
            return None
    
    def load_image(self, image_path: str) -> Optional[Image.Image]:
        """
        Load image from storage.
        
        Args:
            image_path: Path to image file
            
        Returns:
            PIL Image object, or None if failed
        """
        try:
            if not os.path.exists(image_path):
                return None
            
            return Image.open(image_path)
        except Exception:
            return None
    
    def delete_image(self, image_path: str) -> bool:
        """
        Delete image file from storage.
        
        Args:
            image_path: Path to image file to delete
            
        Returns:
            True if successful, False otherwise
        """
        try:
            if os.path.exists(image_path):
                os.remove(image_path)
                return True
            return False
        except Exception:
            return False
    
    def get_image_thumbnail(self, image_path: str, size: tuple = (100, 100)) -> Optional[Image.Image]:
        """
        Get thumbnail version of image.
        
        Args:
            image_path: Path to image file
            size: Thumbnail size as (width, height) tuple
            
        Returns:
            PIL Image thumbnail, or None if failed
        """
        try:
            image = self.load_image(image_path)
            if image is None:
                return None
            
            # Create thumbnail (maintains aspect ratio)
            image.thumbnail(size, Image.Resampling.LANCZOS)
            return image
        except Exception:
            return None
    
    def cleanup_orphaned_images(self, valid_image_paths: list) -> int:
        """
        Delete images that are not referenced in the database.
        
        Args:
            valid_image_paths: List of image paths that should be kept
            
        Returns:
            Number of images deleted
        """
        deleted_count = 0
        
        try:
            # Get all image files in storage directory
            all_images = list(self.storage_dir.glob('*.png'))
            all_images.extend(list(self.storage_dir.glob('*.jpg')))
            all_images.extend(list(self.storage_dir.glob('*.jpeg')))
            
            # Convert valid paths to set for faster lookup
            valid_paths_set = set(valid_image_paths)
            
            # Delete orphaned images
            for image_path in all_images:
                if str(image_path) not in valid_paths_set:
                    try:
                        os.remove(image_path)
                        deleted_count += 1
                    except Exception:
                        pass
            
            return deleted_count
        except Exception:
            return deleted_count
    
    def get_storage_size(self) -> int:
        """
        Get total size of image storage in bytes.
        
        Returns:
            Total size in bytes
        """
        total_size = 0
        
        try:
            for file_path in self.storage_dir.rglob('*'):
                if file_path.is_file():
                    total_size += file_path.stat().st_size
            
            return total_size
        except Exception:
            return 0
    
    def clear_all_images(self) -> bool:
        """
        Delete all images from storage.
        
        Returns:
            True if successful, False otherwise
        """
        try:
            # Remove all files in the directory
            for file_path in self.storage_dir.iterdir():
                if file_path.is_file():
                    file_path.unlink()
            
            return True
        except Exception:
            return False
    
    def __repr__(self) -> str:
        """String representation for debugging."""
        return f"ImageStorage(dir={self.storage_dir}, size={self.get_storage_size()} bytes)"
