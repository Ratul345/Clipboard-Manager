#!/bin/bash
# Build script for Linux executable and packages
# Requires PyInstaller: pip install pyinstaller

echo "========================================"
echo "Building Clipboard Manager for Linux"
echo "========================================"
echo ""

# Check if PyInstaller is installed
if ! python3 -c "import PyInstaller" 2>/dev/null; then
    echo "ERROR: PyInstaller is not installed"
    echo "Please install it with: pip install pyinstaller"
    exit 1
fi

# Generate icons if they don't exist
if [ ! -f "assets/icons/clipboard.png" ]; then
    echo "Generating application icons..."
    python3 assets/icons/create_icons.py
    echo ""
fi

# Clean previous builds
echo "Cleaning previous builds..."
rm -rf build dist
echo ""

# Build executable
echo "Building executable..."
pyinstaller build_linux.spec
echo ""

if [ -f "dist/clipboard-manager" ]; then
    echo "========================================"
    echo "Build completed successfully!"
    echo "========================================"
    echo ""
    echo "Executable location: dist/clipboard-manager"
    echo ""
    
    # Make executable
    chmod +x dist/clipboard-manager
    
    # Create .desktop file
    echo "Creating .desktop file..."
    mkdir -p dist/share/applications
    cat > dist/share/applications/clipboard-manager.desktop << EOF
[Desktop Entry]
Version=1.0
Type=Application
Name=Clipboard Manager
Comment=Manage your clipboard history
Exec=/usr/local/bin/clipboard-manager
Icon=clipboard-manager
Terminal=false
Categories=Utility;
EOF
    
    # Copy icon
    mkdir -p dist/share/icons/hicolor/256x256/apps
    cp assets/icons/clipboard.png dist/share/icons/hicolor/256x256/apps/clipboard-manager.png
    
    echo ""
    echo "To install system-wide:"
    echo "  sudo cp dist/clipboard-manager /usr/local/bin/"
    echo "  sudo cp dist/share/applications/clipboard-manager.desktop /usr/share/applications/"
    echo "  sudo cp dist/share/icons/hicolor/256x256/apps/clipboard-manager.png /usr/share/icons/hicolor/256x256/apps/"
    echo "  sudo update-desktop-database"
    echo ""
    echo "To create a .deb package, install: sudo apt-get install dpkg-dev"
    echo "To create an AppImage, see: https://appimage.org/"
    echo ""
else
    echo "========================================"
    echo "Build failed!"
    echo "========================================"
    echo "Please check the error messages above."
    exit 1
fi
