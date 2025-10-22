"""Configuration manager for the Clipboard Manager application."""

import json
import os
from pathlib import Path
from typing import Any, Dict, Optional


class Config:
    """Manages application configuration with JSON persistence."""
    
    DEFAULT_CONFIG = {
        'auto_start': False,
        'hotkey': 'ctrl+shift+v',
        'max_items': 1000,
        'capture_text': True,
        'capture_images': True,
        'capture_links': True,
        'theme': 'light'
    }
    
    def __init__(self, config_path: Optional[str] = None):
        """
        Initialize Config manager.
        
        Args:
            config_path: Path to config file (defaults to ~/.clipboard-manager/config.json)
        """
        if config_path is None:
            config_dir = Path.home() / '.clipboard-manager'
            config_dir.mkdir(parents=True, exist_ok=True)
            config_path = str(config_dir / 'config.json')
        
        self.config_path = config_path
        self.data = self._load_or_create()
    
    def _load_or_create(self) -> Dict[str, Any]:
        """Load configuration from file or create with defaults."""
        if os.path.exists(self.config_path):
            try:
                with open(self.config_path, 'r', encoding='utf-8') as f:
                    loaded_data = json.load(f)
                    # Merge with defaults to ensure all keys exist
                    config_data = self.DEFAULT_CONFIG.copy()
                    config_data.update(loaded_data)
                    return config_data
            except (json.JSONDecodeError, IOError):
                # If file is corrupted, use defaults
                return self.DEFAULT_CONFIG.copy()
        else:
            # Create new config file with defaults
            config_data = self.DEFAULT_CONFIG.copy()
            self._save(config_data)
            return config_data
    
    def _save(self, data: Optional[Dict[str, Any]] = None) -> bool:
        """
        Save configuration to file.
        
        Args:
            data: Configuration data to save (defaults to self.data)
            
        Returns:
            True if successful, False otherwise
        """
        if data is None:
            data = self.data
        
        try:
            # Ensure directory exists
            os.makedirs(os.path.dirname(self.config_path), exist_ok=True)
            
            with open(self.config_path, 'w', encoding='utf-8') as f:
                json.dump(data, f, indent=2, ensure_ascii=False)
            return True
        except IOError:
            return False
    
    def get(self, key: str, default: Any = None) -> Any:
        """
        Get configuration value.
        
        Args:
            key: Configuration key
            default: Default value if key doesn't exist
            
        Returns:
            Configuration value or default
        """
        return self.data.get(key, default)
    
    def set(self, key: str, value: Any) -> bool:
        """
        Set configuration value and save to file.
        
        Args:
            key: Configuration key
            value: Value to set
            
        Returns:
            True if successful, False otherwise
        """
        # Validate value based on key
        if not self._validate_value(key, value):
            return False
        
        self.data[key] = value
        return self._save()
    
    def _validate_value(self, key: str, value: Any) -> bool:
        """
        Validate configuration value.
        
        Args:
            key: Configuration key
            value: Value to validate
            
        Returns:
            True if valid, False otherwise
        """
        # Type validation based on default config
        if key in self.DEFAULT_CONFIG:
            expected_type = type(self.DEFAULT_CONFIG[key])
            if not isinstance(value, expected_type):
                return False
        
        # Specific validations
        if key == 'max_items':
            return isinstance(value, int) and value > 0 and value <= 10000
        elif key == 'theme':
            return value in ('light', 'dark')
        elif key == 'hotkey':
            return isinstance(value, str) and len(value) > 0
        elif key in ('auto_start', 'capture_text', 'capture_images', 'capture_links'):
            return isinstance(value, bool)
        
        return True
    
    def load_config(self) -> Dict[str, Any]:
        """
        Reload configuration from file.
        
        Returns:
            Current configuration data
        """
        self.data = self._load_or_create()
        return self.data.copy()
    
    def save_config(self) -> bool:
        """
        Save current configuration to file.
        
        Returns:
            True if successful, False otherwise
        """
        return self._save()
    
    def reset_to_defaults(self) -> bool:
        """
        Reset configuration to default values.
        
        Returns:
            True if successful, False otherwise
        """
        self.data = self.DEFAULT_CONFIG.copy()
        return self._save()
    
    def __repr__(self) -> str:
        """String representation for debugging."""
        return f"Config(path={self.config_path}, keys={list(self.data.keys())})"
