"""Conversions between Pillow images and Qt images/pixmaps."""

from __future__ import annotations

from PIL import Image
from PySide6.QtGui import QImage, QPixmap


def pil_to_qpixmap(image: Image.Image) -> QPixmap:
    """Convert a Pillow image to a QPixmap (via RGBA8888)."""
    rgba = image.convert("RGBA")
    data = rgba.tobytes("raw", "RGBA")
    qimage = QImage(data, rgba.width, rgba.height, rgba.width * 4, QImage.Format.Format_RGBA8888)
    # copy() detaches the QImage from the Python-owned buffer before it goes away
    return QPixmap.fromImage(qimage.copy())


def qimage_to_pil(qimage: QImage) -> Image.Image:
    """Convert a QImage to a Pillow RGBA image."""
    converted = qimage.convertToFormat(QImage.Format.Format_RGBA8888)
    # For RGBA8888 each scanline is exactly width * 4 bytes, so the buffer is contiguous.
    buffer = bytes(converted.constBits())
    return Image.frombytes("RGBA", (converted.width(), converted.height()), buffer)
