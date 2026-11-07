"""Vector icons drawn with QPainter.

Drawing the icons keeps the UI free of emoji (which look different on every
platform) and lets every icon follow the active theme colour. Icons are drawn
in a 24x24 coordinate space and scaled to the requested size.
"""

from PyQt5.QtCore import Qt, QPointF, QRectF
from PyQt5.QtGui import QBrush, QColor, QIcon, QPainter, QPainterPath, QPen, QPixmap


def _stroke(color: QColor, width: float = 1.8) -> QPen:
    pen = QPen(color)
    pen.setWidthF(width)
    pen.setCapStyle(Qt.RoundCap)
    pen.setJoinStyle(Qt.RoundJoin)
    return pen


def _polyline(points) -> QPainterPath:
    path = QPainterPath()
    path.moveTo(*points[0])
    for x, y in points[1:]:
        path.lineTo(x, y)
    return path


def _paint(p: QPainter, name: str, c: QColor, filled: bool) -> None:
    p.setPen(_stroke(c))
    p.setBrush(Qt.NoBrush)

    if name == 'search':
        p.drawEllipse(QPointF(11, 11), 6.5, 6.5)
        p.drawLine(QPointF(16, 16), QPointF(21, 21))

    elif name == 'close':
        p.drawLine(QPointF(6, 6), QPointF(18, 18))
        p.drawLine(QPointF(18, 6), QPointF(6, 18))

    elif name == 'trash':
        p.drawLine(QPointF(4, 7), QPointF(20, 7))
        p.drawPath(_polyline([(9, 7), (9, 4), (15, 4), (15, 7)]))
        p.drawPath(_polyline([(6, 7), (7, 20), (17, 20), (18, 7)]))
        p.drawLine(QPointF(10, 11), QPointF(10, 16))
        p.drawLine(QPointF(14, 11), QPointF(14, 16))

    elif name == 'pin':
        body = _polyline([(9, 3), (15, 3), (14.2, 9.5), (17.5, 13), (6.5, 13), (9.8, 9.5)])
        body.closeSubpath()
        if filled:
            p.setBrush(QBrush(c))
        p.drawPath(body)
        p.drawLine(QPointF(12, 13), QPointF(12, 21))

    elif name == 'sliders':
        for y, knob_x in ((7, 9), (12, 15), (17, 8)):
            p.drawLine(QPointF(4, y), QPointF(20, y))
            p.setBrush(QBrush(c))
            p.drawEllipse(QPointF(knob_x, y), 2.2, 2.2)
            p.setBrush(Qt.NoBrush)

    elif name == 'text':
        p.drawLine(QPointF(5, 6), QPointF(19, 6))
        p.drawLine(QPointF(12, 6), QPointF(12, 19))

    elif name == 'link':
        p.save()
        p.translate(12, 12)
        p.rotate(-45)
        p.drawRoundedRect(QRectF(-9.5, -3.5, 11, 7), 3.5, 3.5)
        p.drawRoundedRect(QRectF(-1.5, -3.5, 11, 7), 3.5, 3.5)
        p.restore()

    elif name == 'image':
        p.drawRoundedRect(QRectF(3, 4.5, 18, 15), 2.5, 2.5)
        p.setBrush(QBrush(c))
        p.drawEllipse(QPointF(9, 10), 1.6, 1.6)
        p.setBrush(Qt.NoBrush)
        p.drawPath(_polyline([(4, 18), (9.5, 13), (13.5, 17), (16.5, 14), (20, 17.5)]))

    elif name == 'clipboard':
        p.drawRoundedRect(QRectF(5, 5, 14, 16), 2.5, 2.5)
        p.setBrush(QBrush(c))
        p.drawRoundedRect(QRectF(9, 2.8, 6, 4), 1.5, 1.5)
        p.setBrush(Qt.NoBrush)
        p.drawLine(QPointF(8.5, 12), QPointF(15.5, 12))
        p.drawLine(QPointF(8.5, 16), QPointF(13, 16))

    elif name == 'check':
        p.drawPath(_polyline([(5, 12.5), (10, 17.5), (19, 7.5)]))


def make_pixmap(name: str, color: str, size: int = 18, filled: bool = False,
                device_pixel_ratio: float = 2.0) -> QPixmap:
    """Render an icon to a crisp (HiDPI) pixmap."""
    pixmap = QPixmap(int(size * device_pixel_ratio), int(size * device_pixel_ratio))
    pixmap.setDevicePixelRatio(device_pixel_ratio)
    pixmap.fill(Qt.transparent)

    painter = QPainter(pixmap)
    painter.setRenderHint(QPainter.Antialiasing, True)
    painter.scale(size / 24.0, size / 24.0)
    _paint(painter, name, QColor(color), filled)
    painter.end()
    return pixmap


def make_icon(name: str, color: str, size: int = 18, filled: bool = False) -> QIcon:
    return QIcon(make_pixmap(name, color, size, filled))
