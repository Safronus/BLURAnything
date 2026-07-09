"""Tests for the editor canvas gestures (offscreen, no synthetic mouse events)."""

from __future__ import annotations

from PySide6.QtCore import QPointF
from pytestqt.qtbot import QtBot

from bluranything.core.document import Document
from bluranything.ui.editor_canvas import EditorCanvas, Tool
from tests.helpers import checkerboard


def make_canvas(qtbot: QtBot) -> tuple[EditorCanvas, Document]:
    document = Document(checkerboard((60, 40)))
    canvas = EditorCanvas()
    qtbot.addWidget(canvas)
    canvas.set_document(document)
    return canvas, document


def test_rectangle_gesture_blurs(qtbot: QtBot) -> None:
    canvas, document = make_canvas(qtbot)
    canvas.set_tool(Tool.RECTANGLE)
    canvas.begin_gesture(QPointF(5, 5))
    canvas.extend_gesture(QPointF(30, 25))
    canvas.finish_gesture()
    assert not document.is_empty


def test_ellipse_gesture_blurs(qtbot: QtBot) -> None:
    canvas, document = make_canvas(qtbot)
    canvas.set_tool(Tool.ELLIPSE)
    canvas.begin_gesture(QPointF(5, 5))
    canvas.extend_gesture(QPointF(40, 30))
    canvas.finish_gesture()
    assert not document.is_empty


def test_lasso_gesture_blurs(qtbot: QtBot) -> None:
    canvas, document = make_canvas(qtbot)
    canvas.set_tool(Tool.LASSO)
    canvas.begin_gesture(QPointF(10, 10))
    for point in (QPointF(40, 10), QPointF(40, 30), QPointF(10, 30)):
        canvas.extend_gesture(point)
    canvas.finish_gesture()
    assert not document.is_empty


def test_polygon_gesture_blurs(qtbot: QtBot) -> None:
    canvas, document = make_canvas(qtbot)
    canvas.set_tool(Tool.POLYGON)
    for point in (QPointF(10, 10), QPointF(40, 10), QPointF(25, 30)):
        canvas.begin_gesture(point)
    canvas.finish_polygon()
    assert not document.is_empty


def test_brush_gesture_blurs_and_undoes_as_one(qtbot: QtBot) -> None:
    canvas, document = make_canvas(qtbot)
    canvas.set_tool(Tool.BRUSH)
    canvas.begin_gesture(QPointF(10, 20))
    canvas.extend_gesture(QPointF(25, 20))
    canvas.extend_gesture(QPointF(40, 20))
    canvas.finish_gesture()
    assert not document.is_empty
    document.undo()
    assert document.is_empty


def test_cancel_discards_in_progress_polygon(qtbot: QtBot) -> None:
    canvas, document = make_canvas(qtbot)
    canvas.set_tool(Tool.POLYGON)
    canvas.begin_gesture(QPointF(5, 5))
    canvas.begin_gesture(QPointF(20, 5))
    canvas.cancel()
    canvas.finish_polygon()
    assert document.is_empty


def test_switching_tool_cancels_gesture(qtbot: QtBot) -> None:
    canvas, document = make_canvas(qtbot)
    canvas.set_tool(Tool.POLYGON)
    canvas.begin_gesture(QPointF(5, 5))
    canvas.begin_gesture(QPointF(20, 5))
    canvas.set_tool(Tool.RECTANGLE)  # should drop the pending polygon
    canvas.finish_polygon()
    assert document.is_empty
