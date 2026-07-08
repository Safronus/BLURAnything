"""Tests for Pillow ↔ Qt image conversions."""

from __future__ import annotations

from PySide6.QtWidgets import QApplication

from bluranything.ui.qt_image import pil_to_qpixmap, qimage_to_pil
from bluranything.ui.screenshot import grab_primary_screen
from tests.helpers import checkerboard


def test_pil_qt_roundtrip_preserves_pixels(qapp: QApplication) -> None:
    image = checkerboard((16, 12))
    pixmap = pil_to_qpixmap(image)
    assert (pixmap.width(), pixmap.height()) == (16, 12)

    restored = qimage_to_pil(pixmap.toImage())
    assert restored.size == image.size
    assert restored.tobytes() == image.convert("RGBA").tobytes()


def test_grab_primary_screen_smoke(qapp: QApplication) -> None:
    # Offscreen platforms may or may not expose a grabbable screen; the call
    # must simply not crash and honour its contract.
    result = grab_primary_screen()
    assert result is None or not result.isNull()
