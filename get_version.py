"""
Simple script to print the application version.
Used by build scripts to get the current version.
"""

from version import __version__

if __name__ == "__main__":
    print(__version__)
