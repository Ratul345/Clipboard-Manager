"""ItemCard widget for displaying individual clipboard items."""

import math
import os
import sys
from datetime import datetime
from typing import Optional, Tuple

from PyQt5.QtCore import Qt, QRectF, QSize, pyqtSignal
from PyQt5.QtGui import (
    QColor, QFontMetrics, QImageReader, QPainter, QPainterPath, QPen, QPixmap,
    QTextDocument, QTextOption
)
from PyQt5.QtWidgets import QPushButton, QWidget

# Add parent directory to path to import models
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from models.clipboard_item import ClipboardItem
from search.search_engine import SearchEngine
from ui.icons import make_icon, make_pixmap
from ui.theme import Theme, type_color, ui_font, with_alpha

_THUMBNAIL_CACHE = {}
_THUMBNAIL_CACHE_LIMIT = 300


def _load_thumbnail(path: str, size: int) -> Tuple[Optional[QPixmap], Optional[QSize]]:
    """Load a square, centre-cropped thumbnail and the original image size."""
    try:
        key = (path, size, os.path.getmtime(path))
    except OSError:
        return None, None

    cached = _THUMBNAIL_CACHE.get(key)
    if cached is not None:
        return cached

    reader = QImageReader(path)
    reader.setAutoTransform(True)
    original = reader.size()
    if not original.isValid():
        return None, None

    scaled = original.scaled(size, size, Qt.KeepAspectRatioByExpanding)
    reader.setScaledSize(scaled)
    image = reader.read()
    if image.isNull():
        return None, None

    pixmap = QPixmap.fromImage(image)
    x = max(0, (pixmap.width() - size) // 2)
    y = max(0, (pixmap.height() - size) // 2)
    result = (pixmap.copy(x, y, size, size), original)

    if len(_THUMBNAIL_CACHE) >= _THUMBNAIL_CACHE_LIMIT:
        _THUMBNAIL_CACHE.clear()
    _THUMBNAIL_CACHE[key] = result
    return result


def format_relative_time(moment: datetime) -> str:
    """Short relative time such as '2m ago', or a date for older items."""
    seconds = (datetime.now() - moment).total_seconds()
    if seconds < 60:
        return "just now"
    if seconds < 3600:
        return f"{int(seconds / 60)}m ago"
    if seconds < 86400:
        return f"{int(seconds / 3600)}h ago"
    if seconds < 604800:
        return f"{int(seconds / 86400)}d ago"
    if moment.year == datetime.now().year:
        return moment.strftime("%b %d").replace(" 0", " ")
    return moment.strftime("%b %d, %Y").replace(" 0", " ")


class ItemCard(QWidget):
    """A single clipboard entry: type tile or thumbnail, text excerpt, meta line and actions."""

    delete_clicked = pyqtSignal(ClipboardItem)
    pin_clicked = pyqtSignal(ClipboardItem)
    card_clicked = pyqtSignal(ClipboardItem)
    card_double_clicked = pyqtSignal(ClipboardItem)

    GAP = 3            # transparent space above and below, so cards breathe in a list
    PADDING = 12
    TILE = 40
    ACTIONS_WIDTH = 42
    BUTTON = 26
    MAX_LINES = 3
    MAX_CHARS = 240
    MIN_BODY_HEIGHT = 70

    def __init__(self, clipboard_item: ClipboardItem, search_query: str, theme: Theme,
                 width: int, search_engine: Optional[SearchEngine] = None):
        """
        Args:
            clipboard_item: Item to display
            search_query: Current search text, used to highlight matches
            theme: Active colour theme
            width: Fixed card width in pixels (the card computes its own height)
            search_engine: Optional shared SearchEngine for highlighting
        """
        super().__init__()

        self.clipboard_item = clipboard_item
        self.search_query = search_query or ""
        self.theme = theme
        self.is_selected = False
        self._hover = False
        self._search_engine = search_engine or SearchEngine()

        self._text_x = self.PADDING + self.TILE + 12
        self._text_w = width - self._text_x - self.ACTIONS_WIDTH
        self._thumbnail: Optional[QPixmap] = None
        self._image_size: Optional[QSize] = None

        self._text_font = ui_font(13)
        self._meta_font = ui_font(11)
        self._document = QTextDocument()
        self._visible_text_height = 0.0
        self._meta_text = ""

        self._build_content()

        meta_height = QFontMetrics(self._meta_font).height()
        body = self.PADDING + self._visible_text_height + 6 + meta_height + self.PADDING
        body = max(self.MIN_BODY_HEIGHT, math.ceil(body))
        self.setFixedSize(width, body + 2 * self.GAP)

        self._create_buttons(width)
        self.setCursor(Qt.PointingHandCursor)

    # ----- content -----

    def _build_content(self) -> None:
        item = self.clipboard_item
        t = self.theme

        if item.content_type == 'image':
            if item.image_path and os.path.exists(item.image_path):
                self._thumbnail, self._image_size = _load_thumbnail(item.image_path, self.TILE)
            if self._image_size is not None:
                text = f"Image  {self._image_size.width()} × {self._image_size.height()}"
            else:
                text = "Image"
            html_text = self._search_engine.highlight_html(text, "")
            color = t.text
        else:
            text = self._excerpt(item.content or "", self.search_query)
            highlight_start = (
                f'<span style="background-color:{t.highlight_bg}; color:{t.highlight_fg};">'
            )
            html_text = self._search_engine.highlight_html(
                text, self.search_query, highlight_start, '</span>'
            )
            color = t.type_link if item.content_type == 'link' else t.text

        option = QTextOption()
        option.setWrapMode(QTextOption.WrapAtWordBoundaryOrAnywhere)
        self._document.setDefaultTextOption(option)
        self._document.setDefaultFont(self._text_font)
        self._document.setDocumentMargin(0)
        self._document.setTextWidth(self._text_w)
        self._document.setHtml(f'<div style="color:{color};">{html_text}</div>')

        line_height = QFontMetrics(self._text_font).lineSpacing()
        self._visible_text_height = min(
            self._document.size().height(), line_height * self.MAX_LINES
        )
        self._visible_text_height = max(self._visible_text_height, line_height)

        self._meta_text = self._build_meta()

    @classmethod
    def _excerpt(cls, content: str, query: str) -> str:
        """First few lines of the content, centred on the first search match if needed."""
        content = content.strip()
        if query and query.strip():
            index = content.lower().find(query.lower())
            if index > 120:
                content = "…" + content[index - 40:]

        lines = [line.strip() for line in content.splitlines() if line.strip()]
        text = "\n".join(lines[:cls.MAX_LINES])
        truncated = len(lines) > cls.MAX_LINES
        if len(text) > cls.MAX_CHARS:
            text = text[:cls.MAX_CHARS]
            truncated = True
        if truncated:
            text = text.rstrip() + "…"
        return text

    def _build_meta(self) -> str:
        item = self.clipboard_item
        label = {'link': 'Link', 'image': 'Image'}.get(item.content_type, 'Text')
        parts = [label]
        if item.content_type == 'image' and item.size:
            parts.append(ClipboardItem._format_size(item.size))
        elif item.content_type == 'text' and item.content and len(item.content) > self.MAX_CHARS:
            parts.append(f"{len(item.content):,} chars")
        parts.append(format_relative_time(item.timestamp))
        if item.pinned:
            parts.append("Pinned")
        return "  ·  ".join(parts)

    # ----- actions -----

    def _create_buttons(self, width: int) -> None:
        t = self.theme
        x = width - 8 - self.BUTTON
        top = self.GAP + 8

        self.pin_button = self._make_button(
            'pin', t.accent if self.clipboard_item.pinned else t.text_muted,
            "Unpin" if self.clipboard_item.pinned else "Pin to top",
            filled=self.clipboard_item.pinned
        )
        self.pin_button.move(x, top)
        self.pin_button.clicked.connect(lambda: self.pin_clicked.emit(self.clipboard_item))

        self.delete_button = self._make_button('trash', t.text_muted, "Delete", danger=True)
        self.delete_button.move(x, top + self.BUTTON + 2)
        self.delete_button.clicked.connect(lambda: self.delete_clicked.emit(self.clipboard_item))

    def _make_button(self, icon_name: str, color: str, tooltip: str,
                     filled: bool = False, danger: bool = False) -> QPushButton:
        button = QPushButton(self)
        button.setProperty('variant', 'icon-danger' if danger else 'icon')
        button.setFixedSize(self.BUTTON, self.BUTTON)
        button.setIcon(make_icon(icon_name, color, 15, filled))
        button.setIconSize(QSize(15, 15))
        button.setToolTip(tooltip)
        button.setCursor(Qt.PointingHandCursor)
        button.setFocusPolicy(Qt.NoFocus)
        return button

    def set_selected(self, selected: bool) -> None:
        if self.is_selected != selected:
            self.is_selected = selected
            self.update()

    # ----- painting -----

    def paintEvent(self, event):
        t = self.theme
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)

        body = QRectF(0.5, self.GAP + 0.5, self.width() - 1, self.height() - 2 * self.GAP - 1)
        if self.is_selected:
            fill, border, border_width = t.accent_soft, t.accent, 1.5
        elif self._hover:
            fill, border, border_width = t.surface_hover, t.border_strong, 1
        else:
            fill, border, border_width = t.surface, t.border, 1
        painter.setPen(QPen(QColor(border), border_width))
        painter.setBrush(QColor(fill))
        painter.drawRoundedRect(body, 10, 10)

        self._paint_tile(painter)

        painter.save()
        painter.translate(self._text_x, self.GAP + self.PADDING)
        self._document.drawContents(
            painter, QRectF(0, 0, self._text_w, self._visible_text_height)
        )
        painter.restore()

        meta_top = self.GAP + self.PADDING + self._visible_text_height + 6
        meta_metrics = QFontMetrics(self._meta_font)
        painter.setFont(self._meta_font)
        painter.setPen(QColor(t.text_muted))
        painter.drawText(
            QRectF(self._text_x, meta_top, self._text_w, meta_metrics.height()),
            Qt.AlignLeft | Qt.AlignVCenter,
            meta_metrics.elidedText(self._meta_text, Qt.ElideRight, int(self._text_w))
        )

    def _paint_tile(self, painter: QPainter) -> None:
        t = self.theme
        tile = QRectF(self.PADDING, self.GAP + self.PADDING, self.TILE, self.TILE)

        if self._thumbnail is not None:
            clip = QPainterPath()
            clip.addRoundedRect(tile, 9, 9)
            painter.save()
            painter.setClipPath(clip)
            painter.drawPixmap(int(tile.x()), int(tile.y()), self._thumbnail)
            painter.restore()
            painter.setPen(QPen(with_alpha(t.border_strong, 160), 1))
            painter.setBrush(Qt.NoBrush)
            painter.drawRoundedRect(tile, 9, 9)
            return

        color = type_color(t, self.clipboard_item.content_type)
        painter.setPen(Qt.NoPen)
        painter.setBrush(with_alpha(color, 60 if t.is_dark else 38))
        painter.drawRoundedRect(tile, 9, 9)

        icon_size = 20
        icon = make_pixmap(self.clipboard_item.content_type
                           if self.clipboard_item.content_type in ('text', 'link', 'image')
                           else 'text', color, icon_size)
        painter.drawPixmap(
            int(tile.x() + (self.TILE - icon_size) / 2),
            int(tile.y() + (self.TILE - icon_size) / 2),
            icon
        )

    # ----- events -----

    def enterEvent(self, event):
        self._hover = True
        self.update()
        super().enterEvent(event)

    def leaveEvent(self, event):
        self._hover = False
        self.update()
        super().leaveEvent(event)

    def mousePressEvent(self, event):
        if event.button() == Qt.LeftButton:
            self.card_clicked.emit(self.clipboard_item)
        super().mousePressEvent(event)

    def mouseDoubleClickEvent(self, event):
        if event.button() == Qt.LeftButton:
            self.card_double_clicked.emit(self.clipboard_item)
        super().mouseDoubleClickEvent(event)

    def sizeHint(self) -> QSize:
        return self.size()
