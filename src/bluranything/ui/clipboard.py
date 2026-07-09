"""Reading images from the system clipboard."""

from __future__ import annotations

from PIL import Image
from PySide6.QtGui import QGuiApplication

from bluranything.ui.qt_image import qimage_to_pil


def image_from_clipboard() -> Image.Image | None:
    """Return the clipboard image as a Pillow image, or None if there is none."""
    qimage = QGuiApplication.clipboard().image()
    if qimage.isNull():
        return None
    return qimage_to_pil(qimage)
