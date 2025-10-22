# Build Scripts

This directory contains scripts for building and packaging the Clipboard Manager application for different platforms.

## Prerequisites

### All Platforms
```bash
pip install pyinstaller
```

### Windows
- Python 3.8+
- PyInstaller
- All dependencies from requirements.txt

### Linux
- Python 3.8+
- PyInstaller
- All dependencies from requirements.txt
- For .deb packages: `dpkg-dev`

## Building

### Windows

1. Open Command Prompt in the project root directory
2. Run the build script:
   ```cmd
   build_scripts\build_windows.bat
   ```
3. The executable will be created at `dist\ClipboardManager.exe`

### Linux

1. Open terminal in the project root directory
2. Make the script executable:
   ```bash
   chmod +x build_scripts/build_linux.sh
   ```
3. Run the build script:
   ```bash
   ./build_scripts/build_linux.sh
   ```
4. The executable will be created at `dist/clipboard-manager`

## Creating Packages

### Linux .deb Package

After building the Linux executable:

1. Make the script executable:
   ```bash
   chmod +x build_scripts/create_deb.sh
   ```
2. Run the packaging script:
   ```bash
   ./build_scripts/create_deb.sh
   ```
3. The .deb package will be created in the `dist/` directory

To install the package:
```bash
sudo dpkg -i dist/clipboard-manager_1.0.0_amd64.deb
```

### Windows Installer

For creating a Windows installer, you can use:

1. **Inno Setup** (Recommended)
   - Download from: https://jrsoftware.org/isinfo.php
   - Create an installer script (.iss file)
   - Include the executable and assets

2. **NSIS**
   - Download from: https://nsis.sourceforge.io/
   - Create an installer script (.nsi file)
   - Include the executable and assets

## Testing Builds

### Windows
```cmd
dist\ClipboardManager.exe
```

### Linux
```bash
./dist/clipboard-manager
```

## Troubleshooting

### Missing Dependencies
If the build fails due to missing dependencies, ensure all packages from `requirements.txt` are installed:
```bash
pip install -r requirements.txt
```

### Icon Not Found
If icons are missing, run the icon generation script:
```bash
python assets/icons/create_icons.py
```

### Linux: Missing System Libraries
On Linux, you may need to install additional system libraries:
```bash
# Ubuntu/Debian
sudo apt-get install python3-dev libx11-dev libxcb1-dev

# Fedora
sudo dnf install python3-devel libX11-devel libxcb-devel
```

### Windows: PyWin32 Issues
If you encounter issues with pywin32:
```cmd
pip uninstall pywin32
pip install pywin32
python -m pywin32_postinstall -install
```

## Clean Build

To start fresh:

### Windows
```cmd
rmdir /s /q build dist
```

### Linux
```bash
rm -rf build dist
```

Then run the build script again.
