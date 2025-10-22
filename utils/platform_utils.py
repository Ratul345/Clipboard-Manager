"""Platform detection utilities for cross-platform compatibility."""

import platform
import os


def get_operating_system():
    """
    Detect the current operating system.
    
    Returns:
        str: 'windows', 'linux', or 'unknown'
    """
    system = platform.system().lower()
    if system == 'windows':
        return 'windows'
    elif system == 'linux':
        return 'linux'
    else:
        return 'unknown'


def get_display_server():
    """
    Detect the display server on Linux systems.
    
    Returns:
        str: 'wayland', 'x11', or 'unknown'
    """
    if get_operating_system() != 'linux':
        return 'unknown'
    
    if os.environ.get('WAYLAND_DISPLAY'):
        return 'wayland'
    elif os.environ.get('DISPLAY'):
        return 'x11'
    return 'unknown'


def is_windows():
    """Check if running on Windows."""
    return get_operating_system() == 'windows'


def is_linux():
    """Check if running on Linux."""
    return get_operating_system() == 'linux'


def get_config_directory():
    """
    Get the configuration directory path for the application.
    
    Returns:
        str: Path to config directory (~/.clipboard-manager/)
    """
    home = os.path.expanduser('~')
    return os.path.join(home, '.clipboard-manager')


def get_images_directory():
    """
    Get the images storage directory path.
    
    Returns:
        str: Path to images directory (~/.clipboard-manager/images/)
    """
    return os.path.join(get_config_directory(), 'images')


def get_database_path():
    """
    Get the database file path.
    
    Returns:
        str: Path to database file (~/.clipboard-manager/clipboard.db)
    """
    return os.path.join(get_config_directory(), 'clipboard.db')


def get_config_file_path():
    """
    Get the configuration file path.
    
    Returns:
        str: Path to config file (~/.clipboard-manager/config.json)
    """
    return os.path.join(get_config_directory(), 'config.json')


def get_log_file_path():
    """
    Get the log file path.
    
    Returns:
        str: Path to log file (~/.clipboard-manager/app.log)
    """
    return os.path.join(get_config_directory(), 'app.log')


def ensure_directories_exist():
    """Create necessary directories if they don't exist."""
    config_dir = get_config_directory()
    images_dir = get_images_directory()
    
    os.makedirs(config_dir, exist_ok=True)
    os.makedirs(images_dir, exist_ok=True)
