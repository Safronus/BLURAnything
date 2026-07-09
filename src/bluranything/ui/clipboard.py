"""Reading images from the system clipboard."""

from __future__ import annotations

from PIL import Image
from PySide6.QtGui import QGuiApplication

from bluranything.ui.qt_image import pil_to_qimage, qimage_to_pil


def image_from_clipboard() -> Image.Image | None:
    """Return the clipboard image as a Pillow image, or None if there is none."""
    qimage = QGuiApplication.clipboard().image()
    if qimage.isNull():
        return None
    return qimage_to_pil(qimage)


def image_to_clipboard(image: Image.Image) -> None:
    """Put *image* on the system clipboard."""
    QGuiApplication.clipboard().setImage(pil_to_qimage(image))
