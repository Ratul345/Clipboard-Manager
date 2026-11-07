"""Small reusable widgets shared by the main and settings windows."""

from PyQt5.QtCore import Qt, QRectF, QSize
from PyQt5.QtGui import QColor, QPainter, QPen
from PyQt5.QtWidgets import QAbstractButton, QWidget

from ui.theme import Theme


class Panel(QWidget):
    """Rounded, bordered window background."""

    def __init__(self, theme: Theme, radius: int = 14, parent=None):
        super().__init__(parent)
        self._theme = theme
        self._radius = radius

    def set_theme(self, theme: Theme) -> None:
        self._theme = theme
        self.update()

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)
        rect = QRectF(self.rect()).adjusted(0.5, 0.5, -0.5, -0.5)
        painter.setPen(QPen(QColor(self._theme.border), 1))
        painter.setBrush(QColor(self._theme.bg))
        painter.drawRoundedRect(rect, self._radius, self._radius)


class Card(QWidget):
    """Rounded surface used to group settings rows."""

    def __init__(self, theme: Theme, parent=None):
        super().__init__(parent)
        self._theme = theme

    def set_theme(self, theme: Theme) -> None:
        self._theme = theme
        self.update()

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)
        rect = QRectF(self.rect()).adjusted(0.5, 0.5, -0.5, -0.5)
        painter.setPen(QPen(QColor(self._theme.border), 1))
        painter.setBrush(QColor(self._theme.surface))
        painter.drawRoundedRect(rect, 12, 12)


class Divider(QWidget):
    """One pixel horizontal rule."""

    def __init__(self, theme: Theme, parent=None):
        super().__init__(parent)
        self._theme = theme
        self.setFixedHeight(1)

    def set_theme(self, theme: Theme) -> None:
        self._theme = theme
        self.update()

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.fillRect(self.rect(), QColor(self._theme.border))


class DragHeader(QWidget):
    """Title bar that moves the frameless window when dragged."""

    def __init__(self, parent=None):
        super().__init__(parent)
        self._drag_offset = None

    def mousePressEvent(self, event):
        if event.button() != Qt.LeftButton:
            return
        window = self.window()
        handle = window.windowHandle()
        # Native move works on Wayland and keeps window snapping behaviour
        if handle is not None and hasattr(handle, 'startSystemMove') and handle.startSystemMove():
            return
        self._drag_offset = event.globalPos() - window.frameGeometry().topLeft()

    def mouseMoveEvent(self, event):
        if self._drag_offset is not None and event.buttons() & Qt.LeftButton:
            self.window().move(event.globalPos() - self._drag_offset)

    def mouseReleaseEvent(self, event):
        self._drag_offset = None


class Switch(QAbstractButton):
    """iOS style on/off toggle."""

    def __init__(self, theme: Theme, parent=None):
        super().__init__(parent)
        self._theme = theme
        self.setCheckable(True)
        self.setCursor(Qt.PointingHandCursor)
        self.setFixedSize(40, 22)

    def set_theme(self, theme: Theme) -> None:
        self._theme = theme
        self.update()

    def sizeHint(self) -> QSize:
        return QSize(40, 22)

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)
        track = QColor(self._theme.accent if self.isChecked() else self._theme.border_strong)
        if not self.isEnabled():
            track.setAlpha(110)
        painter.setPen(Qt.NoPen)
        painter.setBrush(track)
        painter.drawRoundedRect(QRectF(0, 0, 40, 22), 11, 11)

        knob_x = 21 if self.isChecked() else 3
        painter.setBrush(QColor('#FFFFFF'))
        painter.drawEllipse(QRectF(knob_x, 3, 16, 16))
