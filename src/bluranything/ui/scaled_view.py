"""A widget that shows an image scaled to fit, with pixel-coordinate mapping.

Shared by the editor canvas and the preview pane so both letterbox the image
identically and agree on how screen positions map to image pixels.
"""

from __future__ import annotations

from PIL import Image
from PySide6.QtCore import QPointF, QRectF, Qt
from PySide6.QtGui import QColor, QPainter, QPaintEvent, QPixmap
from PySide6.QtWidgets import QWidget

from bluranything.ui.qt_image import pil_to_qpixmap

BACKGROUND = QColor("#161616")
PLACEHOLDER_COLOR = QColor("#6b6b6b")


class ScaledImageView(QWidget):
    """Displays a pixmap centered and scaled to fit, keeping aspect ratio."""

    def __init__(self, placeholder: str = "", parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self._pixmap = QPixmap()
        self._placeholder = placeholder
        self.setMinimumSize(240, 240)

    def set_image(self, image: Image.Image | None) -> None:
        self._pixmap = pil_to_qpixmap(image) if image is not None else QPixmap()
        self.update()

    def has_image(self) -> bool:
        return not self._pixmap.isNull()

    def target_rect(self) -> QRectF:
        """Where the image is drawn, in widget coordinates."""
        if self._pixmap.isNull():
            return QRectF()
        scaled = self._pixmap.size().scaled(self.size(), Qt.AspectRatioMode.KeepAspectRatio)
        x = (self.width() - scaled.width()) / 2.0
        y = (self.height() - scaled.height()) / 2.0
        return QRectF(x, y, float(scaled.width()), float(scaled.height()))

    def map_to_image(self, pos: QPointF, *, clamp: bool = False) -> QPointF | None:
        """Map a widget position to image pixel coordinates.

        Returns None when there is no image, or when *pos* is outside it and
        *clamp* is False; with *clamp* the point is pinned to the image bounds.
        """
        rect = self.target_rect()
        if rect.isEmpty():
            return None
        if not clamp and not rect.contains(pos):
            return None
        scale = self._pixmap.width() / rect.width()
        ix = (pos.x() - rect.left()) * scale
        iy = (pos.y() - rect.top()) * scale
        if clamp:
            ix = min(max(ix, 0.0), float(self._pixmap.width()))
            iy = min(max(iy, 0.0), float(self._pixmap.height()))
        return QPointF(ix, iy)

    def image_to_widget(self, point: QPointF) -> QPointF:
        """Inverse of :meth:`map_to_image` (no clamping)."""
        rect = self.target_rect()
        if rect.isEmpty():
            return QPointF()
        scale = rect.width() / self._pixmap.width()
        return QPointF(rect.left() + point.x() * scale, rect.top() + point.y() * scale)

    def paintEvent(self, event: QPaintEvent) -> None:
        painter = QPainter(self)
        painter.fillRect(self.rect(), BACKGROUND)
        if self._pixmap.isNull():
            if self._placeholder:
                painter.setPen(PLACEHOLDER_COLOR)
                painter.drawText(self.rect(), Qt.AlignmentFlag.AlignCenter, self._placeholder)
            return
        painter.setRenderHint(QPainter.RenderHint.SmoothPixmapTransform)
        painter.drawPixmap(self.target_rect(), self._pixmap, QRectF(self._pixmap.rect()))
