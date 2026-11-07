# Clipboard Manager - Release Notes

## Version 1.2.0 - Pinning, Filters, Dark Mode and Bug Fixes

### New
- **Pin items** - Pin from the card or with Ctrl+P. Pinned items stay at the top, are never removed by the history limit and survive "Clear history".
- **Filter chips** - All, Text, Links, Images and Pinned.
- **Dark mode** - Light, Dark or System, chosen in Settings and applied immediately.
- **Image thumbnails** in the list, and images can now be copied back to the clipboard.
- **Live updates** - the open window refreshes when something new is copied.

### Redesign
- New design system (colour tokens, drawn vector icons, consistent spacing) used by every window.
- Cleaner header, search field with leading icon, empty states and a keyboard hint footer.
- Settings rebuilt with grouped cards and toggle switches.
- Window opens centred on the screen that holds the mouse cursor and is dragged with the native window mover (works on Wayland).

### Fixed
- Copied **images were never saved** (a crash when building the preview, and the image saver rejected the data the monitors provide).
- Re-copying something from history **created a duplicate**; it now just moves to the top, and the move is saved.
- Search highlighting rendered clipboard text as HTML (for example `<b>x</b>`); text is now escaped.
- File names and numbers such as `main.py` or `3.14` were classified as links.
- Global hotkey callback ran on a background thread and touched Qt widgets; it now hands over to the GUI thread.
- Deleting items or reaching the history limit left image files on disk.
- Images on the clipboard were re-encoded on every poll, wasting CPU.
- Search treated `%` and `_` as wildcards.
- Quitting from the tray ran shutdown twice.

---

## Version 1.1.0 - UI Redesign

**Release Date:** October 23, 2025

### What's New

This release brings a complete visual overhaul inspired by Windows 11's modern design language, making Clipboard Manager more beautiful and intuitive to use.

### UI/UX Improvements

#### Modern Windows 11 Design
- **Frameless Window** - Sleek borderless design with custom title bar
- **Rounded Corners** - Smooth 12px border-radius throughout the interface
- **Custom Title Bar** - Draggable brand-colored header with integrated controls
- **Fluent Design** - Mica-inspired translucent backgrounds and layered effects

#### Enhanced Main Window
- **Larger Canvas** - Increased to 450x650px for better content visibility
- **Improved Search Bar** - Modern rounded design with integrated search icon
- **Better Spacing** - Consistent 8-12px grid system for cleaner layout
- **Custom Scrollbar** - Minimal, rounded scrollbar that blends seamlessly
- **Items Counter** - Shows total number of clipboard items at a glance

#### Refined Item Cards
- **Smoother Borders** - Lighter colors (#E5E5E5) for subtle separation
- **Better Selection States** - Light blue background (#E8F4FD) when selected
- **Enhanced Hover Effects** - Smooth transitions with brand color accents
- **Improved Delete Button** - Larger, more accessible with better visual feedback

#### Settings Window Redesign
- **Consistent Styling** - Matches main window's modern aesthetic
- **Better Organization** - Cleaner layout with improved spacing
- **Touch-Friendly** - 40px minimum height for all interactive elements

### Visual Design System

#### Color Palette
- **Brand Blue**: #2B7FD8 (primary actions and accents)
- **Light Blue**: #E8F4FD (selection states)
- **Background**: #F3F3F3 (main container)
- **White**: #FFFFFF (cards and inputs)
- **Text**: #1F1F1F (primary), #666666 (secondary)
- **Danger**: #D13438 (delete actions)

#### Typography
- **Font**: Segoe UI (Windows 11 default)
- **Sizes**: 12-14px with proper hierarchy
- **Icons**: Modern emoji-based icons

### User Experience Enhancements

- **Draggable Title Bar** - Click and drag anywhere on the blue header to move window
- **Visual Feedback** - All interactive elements respond to hover and click
- **Smooth Animations** - Subtle transitions for state changes
- **Better Contrast** - Improved readability with optimized color choices
- **Pointer Cursors** - Clear indication of clickable elements

### Technical Details

- All core functionality remains unchanged
- No breaking changes to data storage or configuration
- Backward compatible with v1.0.0 settings and database
- Performance optimizations for smoother UI rendering

### Upgrade Notes

- Simply replace your existing executable with the new version
- All your clipboard history and settings will be preserved
- No manual migration required

### System Requirements

Same as v1.0.0:
- **Windows**: 10 or 11
- **Linux**: X11 or Wayland
- **RAM**: 100MB minimum
- **Disk**: 50MB + clipboard history storage

### Known Issues

None reported. All v1.0.0 functionality working as expected.

### What's Next

Future releases may include:
- Dark theme support
- Pin favorite items
- Categories and tags
- Export/import functionality

---

## Version 1.0.0 - Initial Release

**Release Date:** October 22, 2025

Initial release with core clipboard monitoring, search, and storage functionality. See previous release notes for full v1.0.0 feature list.

---

**Download:** [Latest Release](https://github.com/Ratul345/Clipboard-Manager/releases)
**Support:** Check logs at `~/.clipboard-manager/app.log`
**License:** MIT
