#!/bin/bash
# Script to create a .deb package for Debian/Ubuntu
# Run this after building the Linux executable

VERSION="1.0.0"
PACKAGE_NAME="clipboard-manager"
ARCH="amd64"

echo "========================================"
echo "Creating .deb package"
echo "========================================"
echo ""

# Check if executable exists
if [ ! -f "dist/clipboard-manager" ]; then
    echo "ERROR: Executable not found. Please run build_linux.sh first."
    exit 1
fi

# Create package directory structure
PKG_DIR="dist/${PACKAGE_NAME}_${VERSION}_${ARCH}"
rm -rf "$PKG_DIR"
mkdir -p "$PKG_DIR/DEBIAN"
mkdir -p "$PKG_DIR/usr/local/bin"
mkdir -p "$PKG_DIR/usr/share/applications"
mkdir -p "$PKG_DIR/usr/share/icons/hicolor/256x256/apps"
mkdir -p "$PKG_DIR/usr/share/doc/${PACKAGE_NAME}"

# Create control file
cat > "$PKG_DIR/DEBIAN/control" << EOF
Package: ${PACKAGE_NAME}
Version: ${VERSION}
Section: utils
Priority: optional
Architecture: ${ARCH}
Maintainer: Clipboard Manager Team <team@example.com>
Description: Cross-platform clipboard history manager
 Clipboard Manager captures and stores your clipboard history
 (text, links, and images) and allows you to search, browse,
 and reuse previously copied items.
 .
 Features include:
  - Automatic clipboard monitoring
  - Fast search functionality
  - Image support
  - System tray integration
  - Keyboard navigation
  - Persistent storage
Depends: libc6, libx11-6, libxcb1
EOF

# Create postinst script
cat > "$PKG_DIR/DEBIAN/postinst" << 'EOF'
#!/bin/bash
set -e

# Update desktop database
if [ -x /usr/bin/update-desktop-database ]; then
    update-desktop-database -q
fi

# Update icon cache
if [ -x /usr/bin/gtk-update-icon-cache ]; then
    gtk-update-icon-cache -q -t -f /usr/share/icons/hicolor || true
fi

exit 0
EOF

chmod 755 "$PKG_DIR/DEBIAN/postinst"

# Create postrm script
cat > "$PKG_DIR/DEBIAN/postrm" << 'EOF'
#!/bin/bash
set -e

# Update desktop database
if [ -x /usr/bin/update-desktop-database ]; then
    update-desktop-database -q
fi

# Update icon cache
if [ -x /usr/bin/gtk-update-icon-cache ]; then
    gtk-update-icon-cache -q -t -f /usr/share/icons/hicolor || true
fi

exit 0
EOF

chmod 755 "$PKG_DIR/DEBIAN/postrm"

# Copy files
echo "Copying files..."
cp dist/clipboard-manager "$PKG_DIR/usr/local/bin/"
chmod 755 "$PKG_DIR/usr/local/bin/clipboard-manager"

cp dist/share/applications/clipboard-manager.desktop "$PKG_DIR/usr/share/applications/"
cp dist/share/icons/hicolor/256x256/apps/clipboard-manager.png "$PKG_DIR/usr/share/icons/hicolor/256x256/apps/"

# Create copyright file
cat > "$PKG_DIR/usr/share/doc/${PACKAGE_NAME}/copyright" << EOF
Format: https://www.debian.org/doc/packaging-manuals/copyright-format/1.0/
Upstream-Name: clipboard-manager
Source: https://github.com/yourusername/clipboard-manager

Files: *
Copyright: 2025 Clipboard Manager Team
License: MIT
 Permission is hereby granted, free of charge, to any person obtaining a copy
 of this software and associated documentation files (the "Software"), to deal
 in the Software without restriction, including without limitation the rights
 to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
 copies of the Software, and to permit persons to whom the Software is
 furnished to do so, subject to the following conditions:
 .
 The above copyright notice and this permission notice shall be included in all
 copies or substantial portions of the Software.
 .
 THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
 IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
 FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
 AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
 LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
 OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
 SOFTWARE.
EOF

# Build package
echo "Building package..."
dpkg-deb --build "$PKG_DIR"

if [ -f "${PKG_DIR}.deb" ]; then
    echo ""
    echo "========================================"
    echo "Package created successfully!"
    echo "========================================"
    echo ""
    echo "Package: ${PKG_DIR}.deb"
    echo ""
    echo "To install:"
    echo "  sudo dpkg -i ${PKG_DIR}.deb"
    echo ""
    echo "To uninstall:"
    echo "  sudo apt-get remove ${PACKAGE_NAME}"
    echo ""
else
    echo ""
    echo "========================================"
    echo "Package creation failed!"
    echo "========================================"
    exit 1
fi
