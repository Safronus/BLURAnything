"""Interactive editing canvas (the left pane).

Shows the live rendered result plus a tint over the selected regions and the
shape currently being dragged, and translates mouse gestures into edits on the
:class:`~bluranything.core.document.Document`.
"""

from __future__ import annotations

from PIL import Image
from PySide6.QtCore import QPointF, QRectF, Qt, Signal
from PySide6.QtGui import QColor, QMouseEvent, QPainter, QPaintEvent, QPen, QPixmap
from PySide6.QtWidgets import QWidget

from bluranything.core.document import Document
from bluranything.core.mask import normalize_box
from bluranything.ui.qt_image import pil_to_qpixmap
from bluranything.ui.scaled_view import ScaledImageView

ACCENT = QColor("#0A84FF")
OVERLAY_ALPHA = 0.42


class EditorCanvas(ScaledImageView):
    """Draws the result, a selection tint and the rectangle being dragged."""

    changed = Signal()

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(placeholder="Open an image or paste (⌘V)", parent=parent)
        self._document: Document | None = None
        self._start: QPointF | None = None
        self._current: QPointF | None = None
        self._overlay = QPixmap()

    # ------------------------------------------------------------ public API

    def set_document(self, document: Document | None) -> None:
        self._document = document
        self._start = self._current = None
        self.set_image(document.render() if document is not None else None)
        self._rebuild_overlay()

    def show_result(self, image: Image.Image) -> None:
        """Refresh the displayed result and selection tint after an edit."""
        self.set_image(image)
        self._rebuild_overlay()

    # --------------------------------------------------------------- overlay

    def _rebuild_overlay(self) -> None:
        if self._document is None or self._document.is_empty:
            self._overlay = QPixmap()
            return
        mask = self._document.mask_copy()
        tint = Image.new("RGBA", mask.size, (ACCENT.red(), ACCENT.green(), ACCENT.blue(), 0))
        tint.putalpha(mask.point(lambda v: int(v * OVERLAY_ALPHA)))
        self._overlay = pil_to_qpixmap(tint)

    # ---------------------------------------------------------------- events

    def mousePressEvent(self, event: QMouseEvent) -> None:
        if self._document is None or not self.has_image():
            return
        if event.button() is Qt.MouseButton.LeftButton:
            self._start = self.map_to_image(event.position(), clamp=True)
            self._current = self._start
            self.update()

    def mouseMoveEvent(self, event: QMouseEvent) -> None:
        if self._start is not None:
            self._current = self.map_to_image(event.position(), clamp=True)
            self.update()

    def mouseReleaseEvent(self, event: QMouseEvent) -> None:
        if self._start is None or self._current is None or self._document is None:
            return
        box = (self._start.x(), self._start.y(), self._current.x(), self._current.y())
        self._start = self._current = None
        left, top, right, bottom = normalize_box(box)
        if right - left > 0 and bottom - top > 0:
            self._document.stamp_rectangle(box)
            self.changed.emit()
        else:
            self.update()

    def paintEvent(self, event: QPaintEvent) -> None:
        super().paintEvent(event)
        if not self.has_image():
            return
        painter = QPainter(self)
        rect = self.target_rect()
        if not self._overlay.isNull():
            painter.drawPixmap(rect, self._overlay, QRectF(self._overlay.rect()))
        if self._start is not None and self._current is not None:
            self._draw_active_shape(painter)

    def _draw_active_shape(self, painter: QPainter) -> None:
        assert self._start is not None and self._current is not None
        rect = QRectF(self.image_to_widget(self._start), self.image_to_widget(self._current))
        pen = QPen(ACCENT, 1.5, Qt.PenStyle.DashLine)
        painter.setPen(pen)
        fill = QColor(ACCENT)
        fill.setAlpha(50)
        painter.setBrush(fill)
        painter.drawRect(rect.normalized())
