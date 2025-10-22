@echo off
REM Build script for Windows executable
REM Requires PyInstaller: pip install pyinstaller

echo ========================================
echo Building Clipboard Manager for Windows
echo ========================================
echo.

REM Check if PyInstaller is installed
python -c "import PyInstaller" 2>nul
if errorlevel 1 (
    echo ERROR: PyInstaller is not installed
    echo Please install it with: pip install pyinstaller
    exit /b 1
)

REM Generate icons if they don't exist
if not exist "assets\icons\clipboard.ico" (
    echo Generating application icons...
    python assets\icons\create_icons.py
    echo.
)

REM Clean previous builds
echo Cleaning previous builds...
if exist "build" rmdir /s /q build
if exist "dist" rmdir /s /q dist
echo.

REM Build executable
echo Building executable...
pyinstaller build_windows.spec
echo.

if exist "dist\ClipboardManager.exe" (
    echo ========================================
    echo Build completed successfully!
    echo ========================================
    echo.
    echo Executable location: dist\ClipboardManager.exe
    echo.
    echo To create an installer, you can use:
    echo - Inno Setup: https://jrsoftware.org/isinfo.php
    echo - NSIS: https://nsis.sourceforge.io/
    echo.
) else (
    echo ========================================
    echo Build failed!
    echo ========================================
    echo Please check the error messages above.
    exit /b 1
)
