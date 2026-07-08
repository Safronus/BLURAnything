"""Screen capture helpers."""

from __future__ import annotations

from PySide6.QtGui import QGuiApplication, QImage, QScreen


def grab_primary_screen() -> QImage | None:
    """Grab the primary screen as a QImage.

    Returns ``None`` when no screen is available (e.g. headless platform)
    or when the capture fails (e.g. missing Screen Recording permission).
    """
    # Qt stubs claim primaryScreen() is never None, but headless runs prove otherwise.
    screen: QScreen | None = QGuiApplication.primaryScreen()
    if screen is None:
        return None
    pixmap = screen.grabWindow(0)
    if pixmap.isNull():
        return None
    return pixmap.toImage()
