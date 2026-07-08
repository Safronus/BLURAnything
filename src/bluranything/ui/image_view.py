"""Image canvas with rubber-band region selection."""

from __future__ import annotations

from PySide6.QtCore import QPointF, QRect, QRectF, Qt, Signal
from PySide6.QtGui import QPainter, QPixmap, QResizeEvent
from PySide6.QtWidgets import QGraphicsPixmapItem, QGraphicsScene, QGraphicsView, QWidget


class ImageView(QGraphicsView):
    """Displays the working image and reports dragged selections.

    The pixmap item sits at the scene origin, so scene coordinates map 1:1
    to image pixel coordinates. ``region_selected`` is emitted once per
    completed drag with the selection in image coordinates (unclamped;
    callers clamp to the image bounds).
    """

    region_selected = Signal(QRect)

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self._scene = QGraphicsScene(self)
        self._pixmap_item = QGraphicsPixmapItem()
        self._scene.addItem(self._pixmap_item)
        self.setScene(self._scene)
        self.setDragMode(QGraphicsView.DragMode.RubberBandDrag)
        self.setRenderHint(QPainter.RenderHint.SmoothPixmapTransform)
        self._last_band = QRectF()
        self.rubberBandChanged.connect(self._on_rubber_band_changed)

    def set_pixmap(self, pixmap: QPixmap) -> None:
        self._pixmap_item.setPixmap(pixmap)
        self._scene.setSceneRect(QRectF(pixmap.rect()))
        self.fit()

    def has_image(self) -> bool:
        return not self._pixmap_item.pixmap().isNull()

    def fit(self) -> None:
        if self.has_image():
            self.fitInView(self._pixmap_item, Qt.AspectRatioMode.KeepAspectRatio)

    def resizeEvent(self, event: QResizeEvent) -> None:
        super().resizeEvent(event)
        self.fit()

    def _on_rubber_band_changed(
        self, viewport_rect: QRect, from_scene: QPointF, to_scene: QPointF
    ) -> None:
        if viewport_rect.isNull():
            # Null args signal the end of the drag: emit the accumulated selection.
            rect = self._last_band.toAlignedRect()
            self._last_band = QRectF()
            if not rect.isEmpty() and self.has_image():
                self.region_selected.emit(rect)
        else:
            self._last_band = QRectF(from_scene, to_scene).normalized()
