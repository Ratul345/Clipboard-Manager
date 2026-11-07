"""SettingsWindow - preferences for hotkey, capture, storage and appearance."""

import os
import sys
from typing import Callable, List, Optional, Tuple

from PyQt5.QtCore import QEvent, Qt, pyqtSignal
from PyQt5.QtGui import QColor, QPainter, QPixmap
from PyQt5.QtWidgets import (
    QButtonGroup, QHBoxLayout, QLabel, QLineEdit, QMessageBox, QPushButton,
    QSpinBox, QStackedWidget, QVBoxLayout, QWidget
)

# Add parent directory to path to import models
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from models.config import Config
from ui.icons import make_icon, make_pixmap
from ui.theme import LIGHT, Theme, build_stylesheet, resolve_theme
from ui.widgets import Card, Divider, DragHeader, Panel, Switch
from utils.autostart import AutoStartManager
from version import APP_NAME, __version__ as APP_VERSION

REPO_URL = "https://github.com/Ratul345/Clipboard-Manager"
THEME_OPTIONS = [('light', 'Light'), ('dark', 'Dark'), ('system', 'System')]


class SettingsWindow(QWidget):
    """Frameless settings window with General, Capture, Storage and About pages."""

    # Signals
    settings_changed = pyqtSignal(dict)           # Emitted when settings are saved
    hotkey_changed = pyqtSignal(str)              # Emitted when hotkey is changed
    capture_settings_changed = pyqtSignal(dict)   # Emitted when capture settings change
    storage_limit_changed = pyqtSignal(int)       # Emitted when storage limit changes
    clear_all_requested = pyqtSignal()            # Emitted when clear all data is requested

    WINDOW_WIDTH = 560
    WINDOW_HEIGHT = 560
    MARGIN = 12

    PAGES = ['General', 'Capture', 'Storage', 'About']

    def __init__(self, config: Config, parent=None):
        super().__init__(parent)

        self.config = config
        self.autostart_manager = AutoStartManager()
        self.theme: Theme = resolve_theme(self.config.get('theme', 'light'))

        self._capturing_hotkey = False
        self._themed: List[QWidget] = []      # widgets with a set_theme() method
        self._selected_theme = self.config.get('theme', 'light')

        self._init_ui()
        self._load_settings()
        self.set_theme(self.theme)

    # ------------------------------------------------------------------ UI

    def _init_ui(self) -> None:
        self.setWindowTitle(f"{APP_NAME} Settings")
        self.setWindowFlags(Qt.Window | Qt.WindowStaysOnTopHint | Qt.FramelessWindowHint)
        self.setAttribute(Qt.WA_TranslucentBackground)
        self.setFixedSize(self.WINDOW_WIDTH, self.WINDOW_HEIGHT)

        root = QVBoxLayout(self)
        root.setContentsMargins(self.MARGIN, self.MARGIN, self.MARGIN, self.MARGIN)

        self.panel = Panel(self.theme)
        root.addWidget(self.panel)

        layout = QVBoxLayout(self.panel)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)

        layout.addWidget(self._build_header())
        layout.addLayout(self._build_page_tabs())
        layout.addSpacing(12)

        self.stack = QStackedWidget()
        self.stack.addWidget(self._build_general_page())
        self.stack.addWidget(self._build_capture_page())
        self.stack.addWidget(self._build_storage_page())
        self.stack.addWidget(self._build_about_page())
        stack_row = QHBoxLayout()
        stack_row.setContentsMargins(20, 0, 20, 0)
        stack_row.addWidget(self.stack)
        layout.addLayout(stack_row, 1)

        layout.addLayout(self._build_footer())

    def _build_header(self) -> QWidget:
        header = DragHeader()
        header.setFixedHeight(58)
        row = QHBoxLayout(header)
        row.setContentsMargins(20, 0, 10, 0)

        title = QLabel("Settings")
        title.setProperty('role', 'title')
        row.addWidget(title)
        row.addStretch()

        self.close_button = QPushButton()
        self.close_button.setProperty('variant', 'icon')
        self.close_button.setFixedSize(32, 32)
        self.close_button.setToolTip("Close")
        self.close_button.setCursor(Qt.PointingHandCursor)
        self.close_button.setFocusPolicy(Qt.NoFocus)
        self.close_button.clicked.connect(self.close)
        row.addWidget(self.close_button)
        return header

    def _build_page_tabs(self) -> QHBoxLayout:
        row = QHBoxLayout()
        row.setContentsMargins(20, 0, 20, 0)
        row.setSpacing(6)
        self.page_group = QButtonGroup(self)
        self.page_group.setExclusive(True)

        for index, name in enumerate(self.PAGES):
            button = QPushButton(name)
            button.setCheckable(True)
            button.setProperty('chip', True)
            button.setCursor(Qt.PointingHandCursor)
            button.setFocusPolicy(Qt.NoFocus)
            button.clicked.connect(lambda _c, i=index: self.stack.setCurrentIndex(i))
            self.page_group.addButton(button)
            row.addWidget(button)
            if index == 0:
                button.setChecked(True)
        row.addStretch()
        return row

    def _build_footer(self) -> QHBoxLayout:
        row = QHBoxLayout()
        row.setContentsMargins(20, 12, 20, 18)
        row.setSpacing(10)
        row.addStretch()

        cancel = QPushButton("Cancel")
        cancel.setCursor(Qt.PointingHandCursor)
        cancel.clicked.connect(self.close)
        row.addWidget(cancel)

        self.save_button = QPushButton("Save changes")
        self.save_button.setProperty('variant', 'primary')
        self.save_button.setCursor(Qt.PointingHandCursor)
        self.save_button.setDefault(True)
        self.save_button.clicked.connect(self._on_save_clicked)
        row.addWidget(self.save_button)
        return row

    # ---- building blocks

    def _page(self) -> Tuple[QWidget, QVBoxLayout]:
        page = QWidget()
        layout = QVBoxLayout(page)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(14)
        return page, layout

    def _section(self, parent_layout: QVBoxLayout, title: str,
                 rows: List[QWidget]) -> None:
        label = QLabel(title.upper())
        label.setProperty('role', 'hint')
        parent_layout.addWidget(label)

        card = Card(self.theme)
        self._themed.append(card)
        column = QVBoxLayout(card)
        column.setContentsMargins(0, 0, 0, 0)
        column.setSpacing(0)
        for index, row in enumerate(rows):
            if index:
                divider = Divider(self.theme)
                self._themed.append(divider)
                column.addWidget(divider)
            column.addWidget(row)
        parent_layout.addWidget(card)

    def _row(self, title: str, description: str, control: QWidget) -> QWidget:
        row = QWidget()
        layout = QHBoxLayout(row)
        layout.setContentsMargins(16, 13, 16, 13)
        layout.setSpacing(16)

        text = QVBoxLayout()
        text.setSpacing(2)
        title_label = QLabel(title)
        title_label.setProperty('role', 'rowtitle')
        text.addWidget(title_label)
        if description:
            desc = QLabel(description)
            desc.setProperty('role', 'muted')
            desc.setWordWrap(True)
            text.addWidget(desc)
        layout.addLayout(text, 1)
        layout.addWidget(control, 0, Qt.AlignRight | Qt.AlignVCenter)
        return row

    def _switch(self) -> Switch:
        switch = Switch(self.theme)
        self._themed.append(switch)
        return switch

    # ---- pages

    def _build_general_page(self) -> QWidget:
        page, layout = self._page()

        self.autostart_switch = self._switch()
        self._section(layout, "Startup", [
            self._row("Launch at login",
                      "Start Clipboard Manager automatically when you sign in.",
                      self.autostart_switch)
        ])

        theme_box = QWidget()
        theme_row = QHBoxLayout(theme_box)
        theme_row.setContentsMargins(0, 0, 0, 0)
        theme_row.setSpacing(6)
        self.theme_group = QButtonGroup(self)
        self.theme_group.setExclusive(True)
        self.theme_buttons = {}
        for key, label in THEME_OPTIONS:
            button = QPushButton(label)
            button.setCheckable(True)
            button.setProperty('chip', True)
            button.setCursor(Qt.PointingHandCursor)
            button.setFocusPolicy(Qt.NoFocus)
            button.clicked.connect(lambda _c, k=key: self._on_theme_chosen(k))
            self.theme_group.addButton(button)
            self.theme_buttons[key] = button
            theme_row.addWidget(button)
        self._section(layout, "Appearance", [
            self._row("Theme", "Choose how Clipboard Manager looks.", theme_box)
        ])

        hotkey_box = QWidget()
        hotkey_row = QHBoxLayout(hotkey_box)
        hotkey_row.setContentsMargins(0, 0, 0, 0)
        hotkey_row.setSpacing(8)
        self.hotkey_input = QLineEdit()
        self.hotkey_input.setReadOnly(True)
        self.hotkey_input.setAlignment(Qt.AlignCenter)
        self.hotkey_input.setFixedWidth(150)
        self.hotkey_input.setMinimumHeight(34)
        self.capture_hotkey_button = QPushButton("Change")
        self.capture_hotkey_button.setCursor(Qt.PointingHandCursor)
        self.capture_hotkey_button.clicked.connect(self._on_capture_hotkey_clicked)
        hotkey_row.addWidget(self.hotkey_input)
        hotkey_row.addWidget(self.capture_hotkey_button)
        self._section(layout, "Shortcut", [
            self._row("Open clipboard history",
                      "Click Change, then press the new key combination. Esc cancels.",
                      hotkey_box)
        ])

        layout.addStretch()
        return page

    def _build_capture_page(self) -> QWidget:
        page, layout = self._page()

        self.capture_text_switch = self._switch()
        self.capture_links_switch = self._switch()
        self.capture_images_switch = self._switch()
        self._section(layout, "What to remember", [
            self._row("Text", "Plain text you copy.", self.capture_text_switch),
            self._row("Links", "Web addresses starting with http, https, ftp or www.",
                      self.capture_links_switch),
            self._row("Images", "Screenshots and copied pictures.", self.capture_images_switch),
        ])

        note = QLabel("Turning a type off only affects new copies. Items already in your "
                      "history stay until you delete them.")
        note.setProperty('role', 'muted')
        note.setWordWrap(True)
        layout.addWidget(note)
        layout.addStretch()
        return page

    def _build_storage_page(self) -> QWidget:
        page, layout = self._page()

        self.max_items_spinbox = QSpinBox()
        self.max_items_spinbox.setRange(10, 10000)
        self.max_items_spinbox.setSingleStep(50)
        self.max_items_spinbox.setSuffix(" items")
        self.max_items_spinbox.setButtonSymbols(QSpinBox.NoButtons)
        self.max_items_spinbox.setAlignment(Qt.AlignRight)
        self._section(layout, "History", [
            self._row("History size",
                      "When the limit is reached the oldest items are removed. "
                      "Pinned items are never removed.",
                      self.max_items_spinbox)
        ])

        self.clear_button = QPushButton("Delete everything")
        self.clear_button.setProperty('variant', 'danger')
        self.clear_button.setCursor(Qt.PointingHandCursor)
        self.clear_button.clicked.connect(self._on_clear_all_data_clicked)
        self._section(layout, "Danger zone", [
            self._row("Delete all history",
                      "Permanently removes every item, including pinned ones.",
                      self.clear_button)
        ])

        layout.addStretch()
        return page

    def _build_about_page(self) -> QWidget:
        page, layout = self._page()
        layout.setAlignment(Qt.AlignHCenter)
        layout.addSpacing(18)

        self.about_logo = QLabel()
        self.about_logo.setAlignment(Qt.AlignCenter)
        layout.addWidget(self.about_logo)

        name = QLabel(APP_NAME)
        name.setProperty('role', 'title')
        name.setAlignment(Qt.AlignCenter)
        layout.addWidget(name)

        version = QLabel(f"Version {APP_VERSION}")
        version.setProperty('role', 'muted')
        version.setAlignment(Qt.AlignCenter)
        layout.addWidget(version)

        blurb = QLabel("A fast, private clipboard history for text, links and images. "
                       "Everything stays on your computer.")
        blurb.setProperty('role', 'muted')
        blurb.setAlignment(Qt.AlignCenter)
        blurb.setWordWrap(True)
        layout.addWidget(blurb)

        self.repo_link = QLabel()
        self.repo_link.setAlignment(Qt.AlignCenter)
        self.repo_link.setTextFormat(Qt.RichText)
        self.repo_link.setOpenExternalLinks(True)
        layout.addWidget(self.repo_link)

        layout.addStretch()
        return page

    # --------------------------------------------------------------- theme

    def set_theme(self, theme: Theme) -> None:
        """Apply a colour theme."""
        self.theme = theme
        self.setStyleSheet(build_stylesheet(theme))
        self.panel.set_theme(theme)
        for widget in self._themed:
            widget.set_theme(theme)

        self.close_button.setIcon(make_icon('close', theme.text_muted, 18))
        self.about_logo.setPixmap(self._make_logo(theme))
        self.repo_link.setText(
            f'<a href="{REPO_URL}" style="color:{theme.accent}; text-decoration:none;">'
            f'View source on GitHub</a>'
        )
        self.update()

    @staticmethod
    def _make_logo(theme: Theme) -> QPixmap:
        size, ratio = 56, 2.0
        pixmap = QPixmap(int(size * ratio), int(size * ratio))
        pixmap.setDevicePixelRatio(ratio)
        pixmap.fill(Qt.transparent)
        painter = QPainter(pixmap)
        painter.setRenderHint(QPainter.Antialiasing)
        painter.setPen(Qt.NoPen)
        painter.setBrush(QColor(theme.accent))
        painter.drawRoundedRect(0, 0, size, size, 15, 15)
        painter.drawPixmap(14, 14, make_pixmap('clipboard', theme.on_accent, 28))
        painter.end()
        return pixmap

    def _on_theme_chosen(self, key: str) -> None:
        """Preview the chosen theme immediately; it is saved with the other settings."""
        self._selected_theme = key
        self.set_theme(resolve_theme(key))

    # ------------------------------------------------------------ settings

    def _load_settings(self) -> None:
        """Load current configuration values into the controls."""
        self.autostart_switch.setChecked(self.config.get('auto_start', False))
        self.hotkey_input.setText(self.config.get('hotkey', 'ctrl+shift+v'))

        self._selected_theme = self.config.get('theme', 'light')
        button = self.theme_buttons.get(self._selected_theme, self.theme_buttons['light'])
        button.setChecked(True)

        self.capture_text_switch.setChecked(self.config.get('capture_text', True))
        self.capture_links_switch.setChecked(self.config.get('capture_links', True))
        self.capture_images_switch.setChecked(self.config.get('capture_images', True))

        self.max_items_spinbox.setValue(self.config.get('max_items', 1000))

    # ------------------------------------------------------ hotkey capture

    def _on_capture_hotkey_clicked(self) -> None:
        self.capture_hotkey_button.setText("Press keys…")
        self.capture_hotkey_button.setEnabled(False)

        self.hotkey_input.setReadOnly(False)
        self.hotkey_input.clear()
        self.hotkey_input.setPlaceholderText("Press shortcut")
        self.hotkey_input.installEventFilter(self)
        self.hotkey_input.setFocus()
        self._capturing_hotkey = True

    @staticmethod
    def _key_name(key: int) -> Optional[str]:
        if Qt.Key_A <= key <= Qt.Key_Z:
            return chr(key).lower()
        if Qt.Key_0 <= key <= Qt.Key_9:
            return chr(key)
        if Qt.Key_F1 <= key <= Qt.Key_F12:
            return f"f{key - Qt.Key_F1 + 1}"
        return {
            Qt.Key_Space: 'space',
            Qt.Key_Return: 'enter',
            Qt.Key_Enter: 'enter',
            Qt.Key_Tab: 'tab',
        }.get(key)

    def eventFilter(self, obj, event):
        """Capture the key combination while the hotkey field is listening."""
        if obj is self.hotkey_input and self._capturing_hotkey and event.type() == QEvent.KeyPress:
            key = event.key()
            if key == Qt.Key_Escape:
                self._cancel_hotkey_capture()
                return True

            modifiers = []
            if event.modifiers() & Qt.ControlModifier:
                modifiers.append('ctrl')
            if event.modifiers() & Qt.ShiftModifier:
                modifiers.append('shift')
            if event.modifiers() & Qt.AltModifier:
                modifiers.append('alt')
            if event.modifiers() & Qt.MetaModifier:
                modifiers.append('super')

            key_name = self._key_name(key)
            if modifiers and key_name:
                self.hotkey_input.setText('+'.join(modifiers + [key_name]))
                self._finish_hotkey_capture()
            return True   # swallow every key while capturing

        return super().eventFilter(obj, event)

    def _end_hotkey_capture(self) -> None:
        self._capturing_hotkey = False
        self.hotkey_input.removeEventFilter(self)
        self.hotkey_input.setReadOnly(True)
        self.hotkey_input.setPlaceholderText("")
        self.capture_hotkey_button.setText("Change")
        self.capture_hotkey_button.setEnabled(True)

    def _finish_hotkey_capture(self) -> None:
        self._end_hotkey_capture()

    def _cancel_hotkey_capture(self) -> None:
        self._end_hotkey_capture()
        self.hotkey_input.setText(self.config.get('hotkey', 'ctrl+shift+v'))

    # ------------------------------------------------------------- actions

    def _on_clear_all_data_clicked(self) -> None:
        reply = QMessageBox.question(
            self, 'Delete all history',
            'Delete all clipboard history, including pinned items?\n\n'
            'This action cannot be undone.',
            QMessageBox.Yes | QMessageBox.No, QMessageBox.No
        )
        if reply == QMessageBox.Yes:
            self.clear_all_requested.emit()
            QMessageBox.information(self, 'History deleted',
                                    'All clipboard history has been deleted.')

    def _on_save_clicked(self) -> None:
        if self._capturing_hotkey:
            self._cancel_hotkey_capture()

        hotkey = self.hotkey_input.text().strip()
        if not hotkey:
            QMessageBox.warning(self, 'Invalid shortcut',
                                'Please set a valid shortcut combination.')
            return

        old_hotkey = self.config.get('hotkey')
        hotkey_changed = hotkey != old_hotkey

        # Auto-start (touches the registry / autostart folder, so report failures)
        auto_start_enabled = self.autostart_switch.isChecked()
        old_auto_start = self.config.get('auto_start', False)
        if auto_start_enabled != old_auto_start:
            if auto_start_enabled:
                if not self.autostart_manager.enable_autostart():
                    QMessageBox.warning(self, 'Launch at login failed',
                                        'Could not enable launch at login. Please check permissions.')
                    self.autostart_switch.setChecked(False)
                    auto_start_enabled = False
            elif not self.autostart_manager.disable_autostart():
                QMessageBox.warning(self, 'Launch at login failed',
                                    'Could not disable launch at login.')

        self.config.set('auto_start', auto_start_enabled)
        self.config.set('hotkey', hotkey)
        self.config.set('theme', self._selected_theme)

        capture_settings = {
            'capture_text': self.capture_text_switch.isChecked(),
            'capture_links': self.capture_links_switch.isChecked(),
            'capture_images': self.capture_images_switch.isChecked(),
        }
        for key, value in capture_settings.items():
            self.config.set(key, value)

        max_items = self.max_items_spinbox.value()
        old_max_items = self.config.get('max_items')
        self.config.set('max_items', max_items)

        if hotkey_changed:
            self.hotkey_changed.emit(hotkey)
        self.capture_settings_changed.emit(capture_settings)
        if max_items != old_max_items:
            self.storage_limit_changed.emit(max_items)
        self.settings_changed.emit(self.config.data.copy())

        self.close()

    # -------------------------------------------------------- window events

    def keyPressEvent(self, event):
        if event.key() == Qt.Key_Escape and not self._capturing_hotkey:
            self.close()
            return
        super().keyPressEvent(event)

    def showEvent(self, event):
        """Reload saved values every time the window opens, discarding unsaved edits."""
        self._load_settings()
        saved_theme = resolve_theme(self.config.get('theme', 'light'))
        if saved_theme.name != self.theme.name:
            self.set_theme(saved_theme)
        self.stack.setCurrentIndex(0)
        self.page_group.buttons()[0].setChecked(True)
        super().showEvent(event)

    def closeEvent(self, event):
        if self._capturing_hotkey:
            self._cancel_hotkey_capture()
        # Drop an unsaved theme preview
        saved_theme = resolve_theme(self.config.get('theme', 'light'))
        if saved_theme.name != self.theme.name:
            self.set_theme(saved_theme)
        super().closeEvent(event)
