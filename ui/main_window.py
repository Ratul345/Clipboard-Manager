"""MainWindow - the clipboard history popup."""

import os
import sys
from typing import List, Optional

from PyQt5.QtCore import QEvent, QRectF, Qt, QTimer, pyqtSignal
from PyQt5.QtGui import QColor, QCursor, QGuiApplication, QPainter, QPen, QPixmap
from PyQt5.QtWidgets import (
    QAbstractItemView, QButtonGroup, QHBoxLayout, QLabel, QLineEdit, QListWidget,
    QListWidgetItem, QMessageBox, QPushButton, QVBoxLayout, QWidget
)

# Add parent directory to path to import models
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from models.clipboard_item import ClipboardItem
from search.search_engine import SearchEngine
from storage.storage_manager import StorageManager
from ui.icons import make_icon, make_pixmap
from ui.item_card import ItemCard
from ui.theme import LIGHT, Theme, build_stylesheet
from ui.widgets import DragHeader, Panel


class MainWindow(QWidget):
    """Frameless popup that lists, searches, filters and pastes clipboard history."""

    # Signals
    item_selected = pyqtSignal(ClipboardItem)
    item_deleted = pyqtSignal(int)
    all_items_cleared = pyqtSignal()
    visibility_changed = pyqtSignal(bool)
    settings_requested = pyqtSignal()

    WINDOW_WIDTH = 440
    WINDOW_HEIGHT = 660
    MARGIN = 12              # transparent border that holds the drop shadow
    LIST_LEFT = 14
    LIST_RIGHT = 6
    MAX_RENDERED = 200       # cards drawn at once; search narrows beyond this
    LOAD_LIMIT = 10000

    FILTERS = [
        ('all', 'All'),
        ('text', 'Text'),
        ('link', 'Links'),
        ('image', 'Images'),
        ('pinned', 'Pinned'),
    ]
    DEFAULT_HINT = "Enter paste   ·   Ctrl+P pin   ·   Del remove"

    def __init__(self, storage_manager: StorageManager, search_engine: SearchEngine,
                 theme: Optional[Theme] = None):
        """
        Args:
            storage_manager: Storage used to load, pin, touch and delete items
            search_engine: Engine used to filter items by the search text
            theme: Initial colour theme (defaults to light)
        """
        super().__init__()

        self.storage_manager = storage_manager
        self.search_engine = search_engine
        self.theme = theme or LIGHT

        self.clipboard_items: List[ClipboardItem] = []   # everything in storage
        self.filtered_items: List[ClipboardItem] = []    # after filter + search
        self.visible_items: List[ClipboardItem] = []     # what is drawn as cards
        self.selected_index = -1
        self.active_filter = 'all'

        self._hint_timer = QTimer(self)
        self._hint_timer.setSingleShot(True)
        self._hint_timer.timeout.connect(self._reset_hint)

        self._init_ui()
        self.set_theme(self.theme)

    # ------------------------------------------------------------------ UI

    def _init_ui(self) -> None:
        self.setWindowTitle("Clipboard Manager")
        self.setWindowFlags(Qt.Window | Qt.WindowStaysOnTopHint | Qt.FramelessWindowHint)
        self.setAttribute(Qt.WA_TranslucentBackground)
        self.setFixedSize(self.WINDOW_WIDTH, self.WINDOW_HEIGHT)

        root = QVBoxLayout(self)
        root.setContentsMargins(self.MARGIN, self.MARGIN, self.MARGIN, self.MARGIN)
        root.setSpacing(0)

        self.panel = Panel(self.theme)
        root.addWidget(self.panel)

        layout = QVBoxLayout(self.panel)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)

        layout.addWidget(self._build_header())

        body = QVBoxLayout()
        body.setContentsMargins(self.LIST_LEFT, 0, self.LIST_LEFT, 0)
        body.setSpacing(10)

        self.search_input = QLineEdit()
        self.search_input.setPlaceholderText("Search clipboard history")
        self.search_input.setClearButtonEnabled(True)
        self.search_input.setFixedHeight(40)
        self._search_action = self.search_input.addAction(
            make_icon('search', self.theme.text_muted, 16), QLineEdit.LeadingPosition
        )
        self.search_input.textChanged.connect(self._on_search_changed)
        self.search_input.installEventFilter(self)
        body.addWidget(self.search_input)

        body.addLayout(self._build_filter_row())
        layout.addLayout(body)
        layout.addSpacing(8)

        self.item_list = QListWidget()
        self.item_list.setSelectionMode(QAbstractItemView.NoSelection)
        self.item_list.setFocusPolicy(Qt.NoFocus)
        self.item_list.setVerticalScrollMode(QAbstractItemView.ScrollPerPixel)
        self.item_list.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        self.item_list.verticalScrollBar().setSingleStep(24)
        self.item_list.setSpacing(0)

        list_row = QHBoxLayout()
        list_row.setContentsMargins(self.LIST_LEFT, 0, self.LIST_RIGHT, 0)
        list_row.addWidget(self.item_list)
        layout.addLayout(list_row, 1)

        layout.addWidget(self._build_empty_state(), 1)
        layout.addWidget(self._build_footer())

    def _build_header(self) -> QWidget:
        header = DragHeader()
        header.setFixedHeight(58)
        row = QHBoxLayout(header)
        row.setContentsMargins(16, 0, 10, 0)
        row.setSpacing(10)

        self.logo_label = QLabel()
        self.logo_label.setFixedSize(30, 30)
        row.addWidget(self.logo_label)

        titles = QVBoxLayout()
        titles.setSpacing(0)
        self.title_label = QLabel("Clipboard")
        self.title_label.setProperty('role', 'title')
        self.count_label = QLabel("")
        self.count_label.setProperty('role', 'hint')
        titles.addStretch()
        titles.addWidget(self.title_label)
        titles.addWidget(self.count_label)
        titles.addStretch()
        row.addLayout(titles)
        row.addStretch()

        self.settings_button = self._header_button("Settings")
        self.settings_button.clicked.connect(self.settings_requested.emit)
        self.close_button = self._header_button("Close (Esc)")
        self.close_button.clicked.connect(self.hide)
        row.addWidget(self.settings_button)
        row.addWidget(self.close_button)
        return header

    def _header_button(self, tooltip: str) -> QPushButton:
        button = QPushButton()
        button.setProperty('variant', 'icon')
        button.setFixedSize(32, 32)
        button.setToolTip(tooltip)
        button.setCursor(Qt.PointingHandCursor)
        button.setFocusPolicy(Qt.NoFocus)
        return button

    def _build_filter_row(self) -> QHBoxLayout:
        row = QHBoxLayout()
        row.setSpacing(6)
        self.filter_group = QButtonGroup(self)
        self.filter_group.setExclusive(True)
        self.filter_buttons = {}

        for key, label in self.FILTERS:
            button = QPushButton(label)
            button.setCheckable(True)
            button.setProperty('chip', True)
            button.setCursor(Qt.PointingHandCursor)
            button.setFocusPolicy(Qt.NoFocus)
            button.clicked.connect(lambda _checked, k=key: self._on_filter_changed(k))
            self.filter_group.addButton(button)
            self.filter_buttons[key] = button
            row.addWidget(button)

        self.filter_buttons['all'].setChecked(True)
        row.addStretch()
        return row

    def _build_empty_state(self) -> QWidget:
        self.empty_state = QWidget()
        column = QVBoxLayout(self.empty_state)
        column.setAlignment(Qt.AlignCenter)
        column.setSpacing(6)

        self.empty_icon = QLabel()
        self.empty_icon.setAlignment(Qt.AlignCenter)
        self.empty_title = QLabel()
        self.empty_title.setProperty('role', 'title')
        self.empty_title.setAlignment(Qt.AlignCenter)
        self.empty_body = QLabel()
        self.empty_body.setProperty('role', 'muted')
        self.empty_body.setAlignment(Qt.AlignCenter)
        self.empty_body.setWordWrap(True)

        column.addWidget(self.empty_icon)
        column.addWidget(self.empty_title)
        column.addWidget(self.empty_body)
        self.empty_state.hide()
        return self.empty_state

    def _build_footer(self) -> QWidget:
        footer = QWidget()
        footer.setFixedHeight(46)
        row = QHBoxLayout(footer)
        row.setContentsMargins(self.LIST_LEFT + 2, 0, 10, 4)

        self.hint_label = QLabel(self.DEFAULT_HINT)
        self.hint_label.setProperty('role', 'hint')
        row.addWidget(self.hint_label)
        row.addStretch()

        self.clear_button = QPushButton("Clear history")
        self.clear_button.setProperty('variant', 'ghost-danger')
        self.clear_button.setCursor(Qt.PointingHandCursor)
        self.clear_button.setFocusPolicy(Qt.NoFocus)
        self.clear_button.clicked.connect(self._on_clear_all_clicked)
        row.addWidget(self.clear_button)
        return footer

    # --------------------------------------------------------------- theme

    def set_theme(self, theme: Theme) -> None:
        """Apply a colour theme to the whole window and redraw the list."""
        self.theme = theme
        self.setStyleSheet(build_stylesheet(theme))
        self.panel.set_theme(theme)

        self._search_action.setIcon(make_icon('search', theme.text_muted, 16))
        self.settings_button.setIcon(make_icon('sliders', theme.text_muted, 18))
        self.close_button.setIcon(make_icon('close', theme.text_muted, 18))
        self.logo_label.setPixmap(self._make_logo(theme))
        self.empty_icon.setPixmap(make_pixmap('clipboard', theme.border_strong, 44))

        self.update()
        if self.clipboard_items:
            self._refresh_item_list()

    @staticmethod
    def _make_logo(theme: Theme) -> QPixmap:
        ratio = 2.0
        pixmap = QPixmap(int(30 * ratio), int(30 * ratio))
        pixmap.setDevicePixelRatio(ratio)
        pixmap.fill(Qt.transparent)
        painter = QPainter(pixmap)
        painter.setRenderHint(QPainter.Antialiasing)
        painter.setPen(Qt.NoPen)
        painter.setBrush(QColor(theme.accent))
        painter.drawRoundedRect(QRectF(0, 0, 30, 30), 8, 8)
        painter.drawPixmap(6, 6, make_pixmap('clipboard', theme.on_accent, 18))
        painter.end()
        return pixmap

    def paintEvent(self, event):
        """Soft drop shadow drawn in the transparent margin around the panel."""
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)
        painter.setBrush(Qt.NoBrush)
        base = QRectF(self.rect()).adjusted(
            self.MARGIN, self.MARGIN + 3, -self.MARGIN, -self.MARGIN + 3
        )
        for i in range(1, self.MARGIN):
            alpha = int(self.theme.shadow_alpha * 0.35 * (1 - i / self.MARGIN) ** 2)
            painter.setPen(QPen(QColor(0, 0, 0, alpha), 1))
            painter.drawRoundedRect(base.adjusted(-i, -i, i, i), 14 + i, 14 + i)

    # ------------------------------------------------------------ loading

    def load_items(self) -> None:
        """Reload everything from storage and reset the selection to the first item."""
        self.clipboard_items = self.storage_manager.get_all_items(limit=self.LOAD_LIMIT)
        self._apply_filters()

    def refresh_items(self) -> None:
        """Reload from storage while the window is open (a new item was copied)."""
        if not self.isVisible():
            return
        selected_id = self._selected_item_id()
        self.clipboard_items = self.storage_manager.get_all_items(limit=self.LOAD_LIMIT)
        self._apply_filters(keep_selected_id=selected_id)

    def _apply_filters(self, keep_selected_id: Optional[int] = None,
                       keep_index: Optional[int] = None) -> None:
        items = self.clipboard_items
        if self.active_filter == 'pinned':
            items = [i for i in items if i.pinned]
        elif self.active_filter != 'all':
            items = [i for i in items if i.content_type == self.active_filter]

        query = self.search_input.text()
        if query.strip():
            items = self.search_engine.search(query, items)

        self.filtered_items = items
        self.visible_items = items[:self.MAX_RENDERED]

        index = -1
        if keep_selected_id is not None:
            index = next(
                (n for n, i in enumerate(self.visible_items) if i.id == keep_selected_id), -1
            )
        if index < 0 and keep_index is not None and self.visible_items:
            index = min(keep_index, len(self.visible_items) - 1)
        if index < 0 and self.visible_items:
            index = 0
        self.selected_index = index

        self._refresh_item_list()

    def _card_width(self) -> int:
        panel_width = self.WINDOW_WIDTH - 2 * self.MARGIN
        return panel_width - self.LIST_LEFT - self.LIST_RIGHT - 14   # 14 = scrollbar + gap

    def _refresh_item_list(self) -> None:
        self.item_list.setUpdatesEnabled(False)
        self.item_list.clear()

        query = self.search_input.text()
        width = self._card_width()
        for row, item in enumerate(self.visible_items):
            card = ItemCard(item, query, self.theme, width, self.search_engine)
            card.card_clicked.connect(self._on_card_clicked)
            card.card_double_clicked.connect(lambda _item: self._select_current_item())
            card.pin_clicked.connect(self._toggle_pin)
            card.delete_clicked.connect(self._delete_item)
            card.set_selected(row == self.selected_index)

            list_item = QListWidgetItem(self.item_list)
            list_item.setSizeHint(card.size())
            self.item_list.setItemWidget(list_item, card)

        self.item_list.setUpdatesEnabled(True)
        self._update_empty_state()
        self._update_counts()
        self._scroll_to_selection()

    def _update_empty_state(self) -> None:
        has_items = bool(self.visible_items)
        self.item_list.setVisible(has_items)
        self.empty_state.setVisible(not has_items)
        if has_items:
            return

        if not self.clipboard_items:
            title, body = "Nothing copied yet", "Copy text, links or images and\nthey will show up here."
        elif self.search_input.text().strip():
            title, body = "No matches", "Try a different search or filter."
        elif self.active_filter == 'pinned':
            title, body = "No pinned items", "Pin an item to keep it at the top\nand safe from auto-cleanup."
        else:
            title, body = "Nothing here", "No items of this type yet."
        self.empty_title.setText(title)
        self.empty_body.setText(body)

    def _update_counts(self) -> None:
        total = len(self.clipboard_items)
        shown = len(self.filtered_items)
        noun = "item" if total == 1 else "items"
        if shown != total:
            text = f"{shown} of {total} {noun}"
        else:
            text = f"{total} {noun}"
        if len(self.filtered_items) > len(self.visible_items):
            text += f"  ·  showing newest {len(self.visible_items)}"
        self.count_label.setText(text)
        has_unpinned = any(not i.pinned for i in self.clipboard_items)
        self.clear_button.setEnabled(has_unpinned)

    # ---------------------------------------------------------- selection

    def _selected_item(self) -> Optional[ClipboardItem]:
        if 0 <= self.selected_index < len(self.visible_items):
            return self.visible_items[self.selected_index]
        return None

    def _selected_item_id(self) -> Optional[int]:
        item = self._selected_item()
        return item.id if item else None

    def _set_selected_index(self, index: int) -> None:
        self.selected_index = index
        for row in range(self.item_list.count()):
            card = self.item_list.itemWidget(self.item_list.item(row))
            if card is not None:
                card.set_selected(row == index)
        self._scroll_to_selection()

    def _scroll_to_selection(self) -> None:
        if 0 <= self.selected_index < self.item_list.count():
            self.item_list.scrollToItem(
                self.item_list.item(self.selected_index), QAbstractItemView.EnsureVisible
            )

    def _move_selection(self, delta: int) -> None:
        if not self.visible_items:
            return
        index = self.selected_index + delta if self.selected_index >= 0 else 0
        self._set_selected_index(max(0, min(len(self.visible_items) - 1, index)))

    def _on_card_clicked(self, item: ClipboardItem) -> None:
        for row, candidate in enumerate(self.visible_items):
            if candidate is item or candidate.id == item.id:
                self._set_selected_index(row)
                return

    # ------------------------------------------------------------ actions

    def _select_current_item(self) -> None:
        """Copy the selected item to the clipboard, move it to the top and close."""
        item = self._selected_item()
        if item is None:
            return

        if not item.copy_to_clipboard():
            self._flash("Couldn't copy this item")
            return

        if item.id is not None:
            self.storage_manager.touch_item(item.id)
        self.item_selected.emit(item)
        self.hide()

    def _delete_item(self, item: ClipboardItem) -> None:
        if item.id is None or not self.storage_manager.delete_item(item.id):
            self._flash("Couldn't delete this item")
            return

        position = self.selected_index
        self.clipboard_items = [i for i in self.clipboard_items if i.id != item.id]
        self._apply_filters(keep_index=position)
        self.item_deleted.emit(item.id)

    def _delete_current_item(self) -> None:
        item = self._selected_item()
        if item is not None:
            self._delete_item(item)

    def _toggle_pin(self, item: ClipboardItem) -> None:
        if item.id is None:
            return
        pinned = not item.pinned
        if not self.storage_manager.set_pinned(item.id, pinned):
            self._flash("Couldn't update this item")
            return

        self.clipboard_items = self.storage_manager.get_all_items(limit=self.LOAD_LIMIT)
        self._apply_filters(keep_selected_id=item.id)
        self._flash("Pinned to top" if pinned else "Unpinned")

    def _toggle_pin_current(self) -> None:
        item = self._selected_item()
        if item is not None:
            self._toggle_pin(item)

    def _on_clear_all_clicked(self) -> None:
        pinned_count = sum(1 for i in self.clipboard_items if i.pinned)
        message = "Delete all clipboard history?"
        if pinned_count:
            message += f"\n\nYour {pinned_count} pinned item{'s' if pinned_count != 1 else ''} will be kept."
        else:
            message += "\n\nThis cannot be undone."

        box = QMessageBox(self)
        box.setIcon(QMessageBox.Question)
        box.setWindowTitle("Clear history")
        box.setText(message)
        box.setStandardButtons(QMessageBox.Yes | QMessageBox.Cancel)
        box.setDefaultButton(QMessageBox.Cancel)
        if box.exec_() != QMessageBox.Yes:
            return

        if self.storage_manager.clear_all_items(keep_pinned=True):
            self.load_items()
            self.all_items_cleared.emit()
        else:
            self._flash("Couldn't clear history")

    # ------------------------------------------------------ search/filter

    def _on_search_changed(self, _text: str) -> None:
        self._apply_filters()

    def _on_filter_changed(self, key: str) -> None:
        self.active_filter = key
        self._apply_filters()

    def _flash(self, message: str, milliseconds: int = 2500) -> None:
        self.hint_label.setText(message)
        self._hint_timer.start(milliseconds)

    def _reset_hint(self) -> None:
        self.hint_label.setText(self.DEFAULT_HINT)

    # ----------------------------------------------------------- keyboard

    def _handle_key(self, event) -> bool:
        """Shared keyboard handling. Returns True when the key was consumed."""
        key = event.key()
        modifiers = event.modifiers()

        if key == Qt.Key_Down:
            self._move_selection(1)
            return True
        if key == Qt.Key_Up:
            self._move_selection(-1)
            return True
        if key in (Qt.Key_Return, Qt.Key_Enter):
            self._select_current_item()
            return True
        if key == Qt.Key_Escape:
            if self.search_input.text():
                self.search_input.clear()
            else:
                self.hide()
            return True
        if key == Qt.Key_P and modifiers & Qt.ControlModifier:
            self._toggle_pin_current()
            return True
        if key == Qt.Key_Delete:
            # While typing a search, Delete edits the text instead
            if self.search_input.text() and self.search_input.hasFocus():
                return False
            self._delete_current_item()
            return True
        return False

    def eventFilter(self, obj, event):
        if obj is self.search_input and event.type() == QEvent.KeyPress:
            if self._handle_key(event):
                return True
        return super().eventFilter(obj, event)

    def keyPressEvent(self, event):
        if not self._handle_key(event):
            super().keyPressEvent(event)

    # ------------------------------------------------------ window events

    def showEvent(self, event):
        """Start every session fresh: empty search, All filter, newest item selected."""
        super().showEvent(event)
        self.search_input.blockSignals(True)
        self.search_input.clear()
        self.search_input.blockSignals(False)
        self.active_filter = 'all'
        self.filter_buttons['all'].setChecked(True)

        self.load_items()
        self._center_on_screen()
        self.activateWindow()
        self.search_input.setFocus()
        self.visibility_changed.emit(True)

    def hideEvent(self, event):
        super().hideEvent(event)
        self.visibility_changed.emit(False)

    def _center_on_screen(self) -> None:
        """Centre on the screen that currently holds the mouse cursor."""
        screen = QGuiApplication.screenAt(QCursor.pos()) or QGuiApplication.primaryScreen()
        if screen is None:
            return
        area = screen.availableGeometry()
        self.move(
            area.center().x() - self.width() // 2,
            area.center().y() - self.height() // 2
        )

    def toggle_visibility(self) -> None:
        """Show the window if hidden, hide it if shown."""
        if self.isVisible():
            self.hide()
        else:
            self.show()
            self.raise_()
            self.activateWindow()
