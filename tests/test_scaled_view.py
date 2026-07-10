"""Tests for the shared scaled image view (cache + coordinate mapping)."""

from __future__ import annotations

from PySide6.QtCore import QPointF
from pytestqt.qtbot import QtBot

from bluranything.ui.scaled_view import ScaledImageView
from tests.helpers import checkerboard


def test_set_image_builds_cache_and_paints(qtbot: QtBot) -> None:
    view = ScaledImageView()
    qtbot.addWidget(view)
    view.resize(400, 300)
    view.set_image(checkerboard((40, 30)))
    assert view.has_image()
    view.grab()  # forces a paint through the cached scaled pixmap; must not crash


def test_coordinate_mapping_roundtrips(qtbot: QtBot) -> None:
    view = ScaledImageView()
    qtbot.addWidget(view)
    view.resize(400, 300)
    view.set_image(checkerboard((40, 30)))
    widget_point = view.image_to_widget(QPointF(10, 8))
    back = view.map_to_image(widget_point)
    assert back is not None
    assert abs(back.x() - 10) < 1.0
    assert abs(back.y() - 8) < 1.0


def test_clearing_image_clears_cache(qtbot: QtBot) -> None:
    view = ScaledImageView()
    qtbot.addWidget(view)
    view.set_image(checkerboard((20, 20)))
    view.set_image(None)
    assert not view.has_image()
    view.grab()  # empty view still paints its placeholder without crashing
