# Cross-Platform Testing Checklist

This document provides a comprehensive testing checklist for the Clipboard Manager application across different platforms and scenarios.

## Test Environment Setup

### Windows Testing
- [ ] Windows 10 (version 1909 or later)
- [ ] Windows 11
- [ ] Clean virtual machine or test environment
- [ ] Python 3.8+ installed (for source testing)
- [ ] All dependencies installed

### Linux Testing
- [ ] Ubuntu 20.04 LTS or later (X11)
- [ ] Ubuntu 22.04 LTS or later (Wayland)
- [ ] Fedora (latest) - optional
- [ ] Clean virtual machine or test environment
- [ ] Python 3.8+ installed (for source testing)
- [ ] All dependencies installed

## Installation Testing

### Windows
- [ ] Executable runs without installation
- [ ] No missing DLL errors
- [ ] Application starts successfully
- [ ] System tray icon appears
- [ ] No antivirus false positives

### Linux
- [ ] .deb package installs successfully
- [ ] Standalone executable runs with correct permissions
- [ ] Desktop entry appears in application menu
- [ ] System tray icon appears
- [ ] No missing library errors

## Core Functionality Testing

### Clipboard Monitoring
- [ ] Text copying is detected and stored
- [ ] Image copying (screenshot) is detected and stored
- [ ] URL copying is detected and tagged as link
- [ ] Multiple rapid copies are all captured
- [ ] Duplicate content is handled correctly
- [ ] Very large text (>1MB) is handled
- [ ] Special characters and Unicode are preserved
- [ ] Emoji are captured correctly
- [ ] Multi-line text is preserved

### Storage and Persistence
- [ ] Items are saved to database immediately
- [ ] Images are saved to filesystem
- [ ] Application restart loads previous items
- [ ] Database handles 1000+ items
- [ ] Storage limit (max_items) is enforced
- [ ] Old items are removed when limit is reached
- [ ] Database doesn't corrupt with rapid writes
- [ ] Disk space errors are handled gracefully

### User Interface
- [ ] Main window opens and displays correctly
- [ ] Window size is appropriate (400x600)
- [ ] Items display in reverse chronological order
- [ ] Text preview is truncated correctly
- [ ] Image thumbnails display properly
- [ ] Timestamps show relative time (e.g., "2m ago")
- [ ] Icons show correct content type (📋 🔗 🖼️)
- [ ] Window stays on top when visible
- [ ] Window closes properly with Escape key
- [ ] Window closes when clicking outside (if applicable)

### Search Functionality
- [ ] Search bar accepts input
- [ ] Real-time filtering works as you type
- [ ] Case-insensitive search works
- [ ] Substring matching works correctly
- [ ] Search finds text in content
- [ ] Search finds URLs in links
- [ ] Empty search shows all items
- [ ] Search with no results shows empty state
- [ ] Special characters in search work
- [ ] Search performance is fast (<100ms)

### Item Selection and Reuse
- [ ] Clicking item copies to clipboard
- [ ] Double-clicking item copies and closes window
- [ ] Enter key copies selected item
- [ ] Selected item moves to top of history
- [ ] Window closes after selection
- [ ] Copied item can be pasted immediately
- [ ] Image items copy correctly
- [ ] Link items copy as plain text URL

### Keyboard Navigation
- [ ] Arrow keys navigate through items
- [ ] Up/Down keys work correctly
- [ ] Enter key selects highlighted item
- [ ] Delete key removes selected item
- [ ] Escape key closes window
- [ ] Ctrl+F focuses search bar (if implemented)
- [ ] Tab key navigates UI elements
- [ ] Keyboard navigation is smooth and responsive

### Item Deletion
- [ ] Delete button removes individual item
- [ ] Delete key removes selected item
- [ ] Deleted item disappears from UI
- [ ] Deleted item removed from database
- [ ] Deleted image file is removed from disk
- [ ] "Clear All" button shows confirmation
- [ ] "Clear All" removes all items
- [ ] "Clear All" removes all image files
- [ ] Database is cleaned up properly

### System Tray Integration
- [ ] Tray icon appears on startup
- [ ] Tray icon is visible and recognizable
- [ ] Left-click opens main window
- [ ] Right-click shows context menu
- [ ] "Open" menu item works
- [ ] "Settings" menu item works
- [ ] "Exit" menu item closes application
- [ ] Application minimizes to tray when window closed
- [ ] Application continues running in background
- [ ] Tray icon tooltip shows app name

### Global Hotkey
- [ ] Default hotkey (Ctrl+Shift+V) works
- [ ] Hotkey opens window when closed
- [ ] Hotkey closes window when open (toggle)
- [ ] Hotkey works from any application
- [ ] Hotkey works with window focus elsewhere
- [ ] Custom hotkey can be set in settings
- [ ] Invalid hotkey combinations are rejected
- [ ] Hotkey conflicts are detected
- [ ] Hotkey persists after restart

### Settings Window
- [ ] Settings window opens from tray menu
- [ ] All tabs are accessible
- [ ] Auto-start checkbox works
- [ ] Hotkey input field works
- [ ] Capture toggles (text/images/links) work
- [ ] Max items setting can be changed
- [ ] "Clear All Data" button works
- [ ] Settings are saved immediately
- [ ] Settings persist after restart
- [ ] Invalid settings are validated

### Auto-Start Functionality
- [ ] Auto-start can be enabled in settings
- [ ] Registry entry created (Windows)
- [ ] .desktop file created (Linux)
- [ ] Application starts on system boot
- [ ] Application starts minimized to tray
- [ ] Auto-start can be disabled
- [ ] Registry entry removed when disabled (Windows)
- [ ] .desktop file removed when disabled (Linux)

## Platform-Specific Testing

### Windows Specific
- [ ] Win32 clipboard API works correctly
- [ ] CF_DIB image format is handled
- [ ] Clipboard access retry logic works
- [ ] Registry auto-start works
- [ ] Windows notifications work (if implemented)
- [ ] High DPI displays render correctly
- [ ] Multiple monitors are handled
- [ ] Windows 10 compatibility
- [ ] Windows 11 compatibility

### Linux Specific
- [ ] X11 clipboard access works
- [ ] Wayland clipboard access works
- [ ] xclip integration works (X11)
- [ ] wl-clipboard integration works (Wayland)
- [ ] .desktop file auto-start works
- [ ] System tray works on GNOME
- [ ] System tray works on KDE
- [ ] System tray works on XFCE
- [ ] File permissions are correct
- [ ] XDG directories are used correctly

## Edge Cases and Stress Testing

### Large Content
- [ ] Text >1MB is handled
- [ ] Text >10MB is handled or rejected gracefully
- [ ] Large images (>10MB) are handled
- [ ] Very long URLs work correctly
- [ ] Binary data in clipboard is handled

### Rapid Operations
- [ ] Rapid copying (10+ items/second) works
- [ ] Rapid searching doesn't lag
- [ ] Rapid window open/close works
- [ ] Rapid item selection works
- [ ] No race conditions or crashes

### Storage Limits
- [ ] Reaching max_items limit works correctly
- [ ] Oldest items are removed first
- [ ] Database doesn't grow indefinitely
- [ ] Image directory doesn't grow indefinitely
- [ ] Disk full scenario is handled

### Error Scenarios
- [ ] Clipboard locked by another app
- [ ] Database file is read-only
- [ ] Database file is corrupted
- [ ] Image directory is not writable
- [ ] Config file is corrupted
- [ ] Network drive storage (if applicable)
- [ ] Low disk space warning
- [ ] Out of memory scenario

### Special Content
- [ ] Empty clipboard is handled
- [ ] Null/None content is handled
- [ ] Binary clipboard data is handled
- [ ] Rich text is converted to plain text
- [ ] HTML content is handled
- [ ] File paths in clipboard
- [ ] Multiple clipboard formats simultaneously

## Performance Testing

### Metrics to Measure
- [ ] Clipboard detection latency <500ms
- [ ] Search response time <100ms for 1000 items
- [ ] Window open time <500ms
- [ ] Memory usage <100MB with 1000 items
- [ ] Startup time <2 seconds
- [ ] Database query time <50ms
- [ ] Image load time <200ms

### Performance Tests
- [ ] Application doesn't slow down over time
- [ ] Memory doesn't leak with extended use
- [ ] CPU usage is minimal when idle
- [ ] Database queries are optimized
- [ ] UI remains responsive with 1000+ items
- [ ] Search is fast with large history

## Security and Privacy Testing

### Data Security
- [ ] Data is stored locally only
- [ ] No network connections are made
- [ ] Database file has correct permissions
- [ ] Image files have correct permissions
- [ ] Sensitive data can be deleted
- [ ] "Clear All" completely removes data

### Privacy
- [ ] No telemetry or analytics
- [ ] No data sent to external servers
- [ ] No logging of sensitive content
- [ ] User can control what is captured

## Regression Testing

After any code changes, verify:
- [ ] All core features still work
- [ ] No new crashes introduced
- [ ] Performance hasn't degraded
- [ ] Settings are preserved
- [ ] Database migrations work (if applicable)

## Test Results

### Windows 10
- Date Tested: ___________
- Tester: ___________
- Pass/Fail: ___________
- Notes: ___________

### Windows 11
- Date Tested: ___________
- Tester: ___________
- Pass/Fail: ___________
- Notes: ___________

### Ubuntu (X11)
- Date Tested: ___________
- Tester: ___________
- Pass/Fail: ___________
- Notes: ___________

### Ubuntu (Wayland)
- Date Tested: ___________
- Tester: ___________
- Pass/Fail: ___________
- Notes: ___________

## Known Issues

Document any known issues discovered during testing:

1. Issue: ___________
   - Platform: ___________
   - Severity: ___________
   - Workaround: ___________

2. Issue: ___________
   - Platform: ___________
   - Severity: ___________
   - Workaround: ___________

## Sign-off

- [ ] All critical tests passed
- [ ] All platform-specific tests passed
- [ ] Performance meets requirements
- [ ] No critical bugs found
- [ ] Application ready for release

Tested by: ___________
Date: ___________
Signature: ___________
