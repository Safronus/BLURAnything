"""Tests for Pillow ↔ Qt image conversions and clipboard access."""

from __future__ import annotations

from PySide6.QtGui import QGuiApplication
from PySide6.QtWidgets import QApplication

from bluranything.ui.clipboard import image_from_clipboard, image_to_clipboard
from bluranything.ui.qt_image import pil_to_qimage, pil_to_qpixmap, qimage_to_pil
from tests.helpers import checkerboard


def test_pixmap_has_image_size(qapp: QApplication) -> None:
    pixmap = pil_to_qpixmap(checkerboard((16, 12)))
    assert (pixmap.width(), pixmap.height()) == (16, 12)


def test_qimage_roundtrip_preserves_pixels(qapp: QApplication) -> None:
    image = checkerboard((10, 8))
    restored = qimage_to_pil(pil_to_qimage(image))
    assert restored.tobytes() == image.convert("RGBA").tobytes()


def test_clipboard_roundtrip(qapp: QApplication) -> None:
    image = checkerboard((16, 12))
    QGuiApplication.clipboard().setImage(pil_to_qimage(image))
    out = image_from_clipboard()
    assert out is not None
    assert out.size == image.size
    assert out.tobytes() == image.convert("RGBA").tobytes()


def test_copy_helper_roundtrip(qapp: QApplication) -> None:
    image = checkerboard((12, 10))
    image_to_clipboard(image)
    out = image_from_clipboard()
    assert out is not None
    assert out.size == (12, 10)
