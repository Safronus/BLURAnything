"""Interactive editing canvas (the left pane).

Shows the live rendered result, a tint over the selected regions and the shape
currently being drawn, and turns mouse gestures into edits on the
:class:`~bluranything.core.document.Document`.

Gestures are exposed as plain methods taking image-space points
(:meth:`begin_gesture`, :meth:`extend_gesture`, :meth:`finish_gesture`,
:meth:`finish_polygon`, :meth:`cancel`) so tool behaviour is unit-testable
without synthesising Qt mouse events.
"""

from __future__ import annotations

from enum import Enum
from itertools import pairwise
from pathlib import Path

from PIL import Image
from PySide6.QtCore import QMimeData, QPointF, QRectF, Qt, Signal
from PySide6.QtGui import (
    QColor,
    QDragEnterEvent,
    QDragLeaveEvent,
    QDragMoveEvent,
    QDropEvent,
    QKeyEvent,
    QMouseEvent,
    QPainter,
    QPaintEvent,
    QPen,
    QPixmap,
)
from PySide6.QtWidgets import QWidget

from bluranything.core.document import Document
from bluranything.core.imageio import INPUT_EXTENSIONS
from bluranything.core.mask import Point
from bluranything.ui import strings
from bluranything.ui.qt_image import pil_to_qpixmap
from bluranything.ui.scaled_view import ScaledImageView

ACCENT = QColor("#0A84FF")
OVERLAY_ALPHA = 0.42
DEFAULT_BRUSH_RADIUS = 16
LASSO_MIN_STEP = 2.0  # min image-space distance between recorded lasso points


class Tool(Enum):
    """The active editing tool."""

    RECTANGLE = "rectangle"
    ELLIPSE = "ellipse"
    POLYGON = "polygon"
    LASSO = "lasso"
    BRUSH = "brush"


def _pt(point: QPointF) -> Point:
    return (point.x(), point.y())


class EditorCanvas(ScaledImageView):
    """Draws the result, a selection tint and the in-progress shape."""

    changed = Signal()
    #: Emitted with the path of an image file dropped onto the canvas.
    file_dropped = Signal(str)

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(placeholder=strings.PLACEHOLDER_EDITOR, parent=parent)
        self.setMouseTracking(True)
        self.setAcceptDrops(True)
        self._drag_active = False
        self._document: Document | None = None
        self._tool = Tool.RECTANGLE
        self._brush_radius = DEFAULT_BRUSH_RADIUS
        self._active = False
        self._start: QPointF | None = None
        self._current: QPointF | None = None
        self._last: QPointF | None = None
        self._vertices: list[QPointF] = []
        self._hover: QPointF | None = None
        self._overlay = QPixmap()

    # ------------------------------------------------------------ public API

    def set_document(self, document: Document | None) -> None:
        self.cancel()
        self._document = document
        self.set_image(document.render() if document is not None else None)
        self._rebuild_overlay()

    def show_result(self, image: Image.Image) -> None:
        """Refresh the displayed result and selection tint after an edit."""
        self.set_image(image)
        self._rebuild_overlay()

    def set_tool(self, tool: Tool) -> None:
        self.cancel()
        self._tool = tool
        self.update()

    def set_brush_radius(self, radius: int) -> None:
        self._brush_radius = max(1, radius)
        self.update()

    # ------------------------------------------------------------- gestures

    def begin_gesture(self, point: QPointF) -> None:
        if self._document is None:
            return
        if self._tool is Tool.POLYGON:
            self._vertices.append(point)
            self._current = point
            self.update()
            return
        self._active = True
        self._start = self._current = point
        if self._tool is Tool.BRUSH:
            self._document.stamp_brush([_pt(point)], self._brush_radius, new_stroke=True)
            self._last = point
            self.changed.emit()
        elif self._tool is Tool.LASSO:
            self._vertices = [point]

    def extend_gesture(self, point: QPointF) -> None:
        self._current = point
        if not self._active:
            if self._tool is Tool.POLYGON:
                self.update()
            return
        if self._tool is Tool.BRUSH and self._document is not None and self._last is not None:
            self._document.stamp_brush(
                [_pt(self._last), _pt(point)], self._brush_radius, new_stroke=False
            )
            self._last = point
            self.changed.emit()
        elif self._tool is Tool.LASSO:
            if not self._vertices or _far_enough(self._vertices[-1], point, LASSO_MIN_STEP):
                self._vertices.append(point)
                self.update()
        else:
            self.update()

    def finish_gesture(self) -> None:
        if not self._active or self._document is None:
            return
        self._active = False
        if self._tool is Tool.RECTANGLE:
            self._commit_bbox(self._document.stamp_rectangle)
        elif self._tool is Tool.ELLIPSE:
            self._commit_bbox(self._document.stamp_ellipse)
        elif self._tool is Tool.LASSO:
            self._commit_polygon(self._vertices)
        self._start = self._current = self._last = None
        self._vertices = []
        self.update()

    def finish_polygon(self) -> None:
        if self._tool is Tool.POLYGON and self._document is not None:
            self._commit_polygon(_dedupe(self._vertices))
        self._vertices = []
        self._current = None
        self.update()

    def cancel(self) -> None:
        self._active = False
        self._start = self._current = self._last = None
        self._vertices = []
        self.update()

    def _commit_bbox(self, stamp: object) -> None:
        if self._start is None or self._current is None:
            return
        box = (self._start.x(), self._start.y(), self._current.x(), self._current.y())
        if abs(box[2] - box[0]) >= 1 and abs(box[3] - box[1]) >= 1:
            stamp(box)  # type: ignore[operator]
            self.changed.emit()

    def _commit_polygon(self, vertices: list[QPointF]) -> None:
        if self._document is not None and len(vertices) >= 3:
            self._document.stamp_polygon([_pt(v) for v in vertices])
            self.changed.emit()

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
            point = self.map_to_image(event.position(), clamp=True)
            if point is not None:
                self.begin_gesture(point)

    def mouseMoveEvent(self, event: QMouseEvent) -> None:
        self._hover = event.position()
        point = self.map_to_image(event.position(), clamp=True)
        if point is not None:
            self.extend_gesture(point)
        elif self._tool is Tool.BRUSH:
            self.update()

    def mouseReleaseEvent(self, event: QMouseEvent) -> None:
        if event.button() is Qt.MouseButton.LeftButton:
            self.finish_gesture()

    def mouseDoubleClickEvent(self, event: QMouseEvent) -> None:
        if self._tool is Tool.POLYGON:
            self.finish_polygon()

    def keyPressEvent(self, event: QKeyEvent) -> None:
        if event.key() == Qt.Key.Key_Escape:
            self.cancel()
        else:
            super().keyPressEvent(event)

    def leaveEvent(self, event: object) -> None:
        self._hover = None
        self.update()

    # ------------------------------------------------------------ drag & drop

    @staticmethod
    def _dropped_image_path(mime: QMimeData) -> Path | None:
        """First local image file among the dragged URLs, if any."""
        if not mime.hasUrls():
            return None
        for url in mime.urls():
            if url.isLocalFile():
                path = Path(url.toLocalFile())
                if path.suffix.lower() in INPUT_EXTENSIONS:
                    return path
        return None

    def dragEnterEvent(self, event: QDragEnterEvent) -> None:
        if self._dropped_image_path(event.mimeData()) is not None:
            self._drag_active = True
            self.update()
            event.acceptProposedAction()
        else:
            event.ignore()

    def dragMoveEvent(self, event: QDragMoveEvent) -> None:
        if self._drag_active:
            event.acceptProposedAction()
        else:
            event.ignore()

    def dragLeaveEvent(self, event: QDragLeaveEvent) -> None:
        self._drag_active = False
        self.update()

    def dropEvent(self, event: QDropEvent) -> None:
        self._drag_active = False
        self.update()
        path = self._dropped_image_path(event.mimeData())
        if path is not None:
            event.acceptProposedAction()
            self.file_dropped.emit(str(path))
        else:
            event.ignore()

    # ---------------------------------------------------------------- paint

    def paintEvent(self, event: QPaintEvent) -> None:
        super().paintEvent(event)
        painter = QPainter(self)
        if self.has_image():
            if not self._overlay.isNull():
                painter.drawPixmap(self.target_rect(), self._overlay, QRectF(self._overlay.rect()))
            self._draw_active_shape(painter)
        if self._drag_active:
            self._draw_drop_hint(painter)

    def _draw_drop_hint(self, painter: QPainter) -> None:
        border = QRectF(self.rect()).adjusted(8, 8, -8, -8)
        fill = QColor(ACCENT)
        fill.setAlpha(28)
        painter.setBrush(fill)
        painter.setPen(QPen(ACCENT, 2, Qt.PenStyle.DashLine))
        painter.drawRoundedRect(border, 12, 12)
        painter.setPen(ACCENT)
        painter.drawText(self.rect(), Qt.AlignmentFlag.AlignCenter, strings.DROP_HINT)

    def _draw_active_shape(self, painter: QPainter) -> None:
        painter.setPen(QPen(ACCENT, 1.5, Qt.PenStyle.DashLine))
        fill = QColor(ACCENT)
        fill.setAlpha(50)
        painter.setBrush(fill)

        if self._tool is Tool.BRUSH:
            self._draw_brush_cursor(painter)
        elif self._active and self._start is not None and self._current is not None:
            rect = QRectF(self.image_to_widget(self._start), self.image_to_widget(self._current))
            if self._tool is Tool.ELLIPSE:
                painter.drawEllipse(rect.normalized())
            elif self._tool is Tool.RECTANGLE:
                painter.drawRect(rect.normalized())
        if self._tool in (Tool.POLYGON, Tool.LASSO):
            self._draw_vertices(painter)

    def _draw_vertices(self, painter: QPainter) -> None:
        points = [self.image_to_widget(v) for v in self._vertices]
        if self._tool is Tool.POLYGON and self._current is not None and points:
            points = [*points, self.image_to_widget(self._current)]
        painter.setBrush(Qt.BrushStyle.NoBrush)
        painter.setPen(QPen(ACCENT, 1.5))
        for a, b in pairwise(points):
            painter.drawLine(a, b)

    def _draw_brush_cursor(self, painter: QPainter) -> None:
        if self._hover is None:
            return
        scale = self.target_rect().width() / self._pixmap.width() if self.has_image() else 1.0
        radius = self._brush_radius * scale
        painter.drawEllipse(self._hover, radius, radius)


def _dedupe(points: list[QPointF]) -> list[QPointF]:
    """Drop consecutive duplicate points (e.g. from a finishing double-click)."""
    out: list[QPointF] = []
    for point in points:
        if not out or abs(point.x() - out[-1].x()) > 0.5 or abs(point.y() - out[-1].y()) > 0.5:
            out.append(point)
    return out


def _far_enough(a: QPointF, b: QPointF, min_step: float) -> bool:
    """True when *a* and *b* are at least *min_step* pixels apart."""
    dx = a.x() - b.x()
    dy = a.y() - b.y()
    return dx * dx + dy * dy >= min_step * min_step
