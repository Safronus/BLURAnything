"""Tests for the editor canvas gestures (offscreen, no synthetic mouse events)."""

from __future__ import annotations

from pathlib import Path

from PySide6.QtCore import QMimeData, QPoint, QPointF, Qt, QUrl
from PySide6.QtGui import QDragEnterEvent, QDropEvent
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


def _url_mime(path: Path) -> QMimeData:
    mime = QMimeData()
    mime.setUrls([QUrl.fromLocalFile(str(path))])
    return mime


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


def test_lasso_thins_dense_points(qtbot: QtBot) -> None:
    canvas, _ = make_canvas(qtbot)
    canvas.set_tool(Tool.LASSO)
    canvas.begin_gesture(QPointF(10, 10))
    for i in range(1, 60):
        canvas.extend_gesture(QPointF(10 + i * 0.1, 10))  # sub-pixel steps
    # near-duplicate points are dropped so the outline stays light and smooth
    assert len(canvas._vertices) < 12


def test_drag_enter_accepts_image_file(qtbot: QtBot, tmp_path: Path) -> None:
    canvas, _ = make_canvas(qtbot)
    image = tmp_path / "photo.png"
    checkerboard((10, 10)).save(image)
    mime = _url_mime(image)  # keep a reference: the event only borrows it
    event = QDragEnterEvent(
        QPoint(5, 5),
        Qt.DropAction.CopyAction,
        mime,
        Qt.MouseButton.LeftButton,
        Qt.KeyboardModifier.NoModifier,
    )
    canvas.dragEnterEvent(event)
    assert event.isAccepted()


def test_drag_enter_rejects_non_image_file(qtbot: QtBot, tmp_path: Path) -> None:
    canvas, _ = make_canvas(qtbot)
    text = tmp_path / "notes.txt"
    text.write_text("nope")
    mime = _url_mime(text)
    event = QDragEnterEvent(
        QPoint(5, 5),
        Qt.DropAction.CopyAction,
        mime,
        Qt.MouseButton.LeftButton,
        Qt.KeyboardModifier.NoModifier,
    )
    canvas.dragEnterEvent(event)
    assert not event.isAccepted()


def test_drop_emits_file_path(qtbot: QtBot, tmp_path: Path) -> None:
    canvas, _ = make_canvas(qtbot)
    image = tmp_path / "dropped.png"
    checkerboard((12, 12)).save(image)
    mime = _url_mime(image)
    event = QDropEvent(
        QPointF(5, 5),
        Qt.DropAction.CopyAction,
        mime,
        Qt.MouseButton.LeftButton,
        Qt.KeyboardModifier.NoModifier,
    )
    with qtbot.waitSignal(canvas.file_dropped) as blocker:
        canvas.dropEvent(event)
    assert blocker.args == [str(image)]
