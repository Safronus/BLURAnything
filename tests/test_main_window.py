"""GUI tests for the main window (offscreen)."""

from __future__ import annotations

from pathlib import Path

import pytest
from PIL import Image
from PySide6.QtCore import QMimeData, QPointF, Qt, QUrl
from PySide6.QtGui import QDropEvent
from PySide6.QtWidgets import QMessageBox
from pytestqt.qtbot import QtBot

from bluranything.core import session
from bluranything.core.mask import new_mask, stamp_rectangle
from bluranything.ui.clipboard import image_from_clipboard
from bluranything.ui.main_window import MainWindow
from tests.helpers import checkerboard


def _reset_dirty(window: MainWindow) -> None:
    # Clear every item's dirty flag before qtbot closes the window at teardown,
    # so the confirm dialog never opens and blocks the headless run.
    for item in window._items:
        item.dirty = False


@pytest.fixture
def window(qtbot: QtBot, tmp_path: Path) -> MainWindow:
    win = MainWindow(autosave_dir=tmp_path / "autosave")
    qtbot.addWidget(win, before_close_func=_reset_dirty)
    return win


@pytest.fixture
def image_file(tmp_path: Path) -> Path:
    path = tmp_path / "input.png"
    checkerboard((40, 30)).save(path)
    return path


@pytest.fixture
def two_images(tmp_path: Path) -> list[Path]:
    paths = []
    for i in range(2):
        path = tmp_path / f"img{i}.png"
        checkerboard((30 + i * 4, 20 + i * 4)).save(path)
        paths.append(path)
    return paths


def test_initial_state_has_no_document(window: MainWindow) -> None:
    assert window.document is None
    assert not window._save_action.isEnabled()
    assert "BLURAnything" in window.windowTitle()


def test_load_enables_editing(window: MainWindow, image_file: Path) -> None:
    assert window.load_path(image_file)
    doc = window.document
    assert doc is not None
    assert doc.size == (40, 30)
    assert window._save_action.isEnabled()
    assert not window.isWindowModified()


def test_dialogs_default_to_source_folder(window: MainWindow, image_file: Path) -> None:
    window.load_path(image_file)
    assert window._default_dir() == image_file.parent


def test_load_missing_file_reports_error(
    window: MainWindow, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    errors: list[str] = []
    monkeypatch.setattr(
        "bluranything.ui.main_window.QMessageBox.critical",
        lambda *args: errors.append(str(args[2])),
    )
    assert not window.load_path(tmp_path / "missing.png")
    assert window.document is None
    assert len(errors) == 1


def test_blur_marks_dirty(window: MainWindow, image_file: Path) -> None:
    window.load_path(image_file)
    doc = window.document
    assert doc is not None
    doc.stamp_rectangle((5, 5, 25, 20))
    window.editor.changed.emit()
    assert window.isWindowModified()
    assert window._undo_action.isEnabled()


def test_undo_restores_empty(window: MainWindow, image_file: Path) -> None:
    window.load_path(image_file)
    doc = window.document
    assert doc is not None
    doc.stamp_rectangle((5, 5, 25, 20))
    window.editor.changed.emit()
    window.undo()
    assert doc.is_empty
    assert not window._undo_action.isEnabled()


def test_paste_from_clipboard(window: MainWindow, monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(
        "bluranything.ui.main_window.image_from_clipboard",
        lambda: checkerboard((20, 16)),
    )
    assert window.paste_from_clipboard()
    doc = window.document
    assert doc is not None
    assert doc.size == (20, 16)


def test_paste_without_image_informs(window: MainWindow, monkeypatch: pytest.MonkeyPatch) -> None:
    infos: list[str] = []
    monkeypatch.setattr("bluranything.ui.main_window.image_from_clipboard", lambda: None)
    monkeypatch.setattr(
        "bluranything.ui.main_window.QMessageBox.information",
        lambda *args: infos.append(str(args[2])),
    )
    assert not window.paste_from_clipboard()
    assert window.document is None
    assert len(infos) == 1


def test_save_writes_file_and_clears_dirty(
    window: MainWindow, image_file: Path, tmp_path: Path
) -> None:
    window.load_path(image_file)
    doc = window.document
    assert doc is not None
    doc.stamp_rectangle((0, 0, 40, 30))
    window.editor.changed.emit()

    out = tmp_path / "out.png"
    assert window.save_to(out)
    assert not window.isWindowModified()
    with Image.open(out) as saved:
        assert saved.size == (40, 30)


def test_clear_removes_regions(window: MainWindow, image_file: Path) -> None:
    window.load_path(image_file)
    doc = window.document
    assert doc is not None
    doc.stamp_rectangle((5, 5, 25, 20))
    window.editor.changed.emit()
    window.clear()
    assert doc.is_empty


def test_effect_selector_updates_document(window: MainWindow, image_file: Path) -> None:
    from bluranything.core.effects import PixelateEffect, SolidFillEffect

    window.load_path(image_file)
    doc = window.document
    assert doc is not None

    window._effect_combo.setCurrentIndex(1)  # Pixelate
    assert isinstance(doc.effect, PixelateEffect)
    assert window._intensity.isEnabled()

    window._effect_combo.setCurrentIndex(2)  # Solid fill
    assert isinstance(doc.effect, SolidFillEffect)
    assert not window._intensity.isEnabled()  # solid fill has no intensity


def test_tool_selector_toggles_brush_size(window: MainWindow) -> None:
    window._tool_combo.setCurrentIndex(4)  # Brush
    assert window._brush.isEnabled()
    window._tool_combo.setCurrentIndex(0)  # Rectangle
    assert not window._brush.isEnabled()


def test_blur_all_faces_stamps_detected(
    window: MainWindow, image_file: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    window.load_path(image_file)
    doc = window.document
    assert doc is not None
    monkeypatch.setattr(
        "bluranything.core.faces.face_boxes", lambda *args, **kwargs: [(2, 2, 20, 20)]
    )
    window.blur_all_faces()
    assert not doc.is_empty
    assert window.isWindowModified()


def test_blur_all_faces_reports_when_none(
    window: MainWindow, image_file: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    window.load_path(image_file)
    doc = window.document
    assert doc is not None
    monkeypatch.setattr("bluranything.core.faces.face_boxes", lambda *args, **kwargs: [])
    window.blur_all_faces()
    assert doc.is_empty


def test_face_tool_click_blurs_single_face(
    window: MainWindow, image_file: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    window.load_path(image_file)
    doc = window.document
    assert doc is not None
    monkeypatch.setattr("bluranything.core.faces.face_at", lambda *args, **kwargs: (2, 2, 20, 20))
    window._on_face_clicked(QPointF(10, 10))
    assert not doc.is_empty
    assert window.isWindowModified()


def test_face_tool_click_without_face(
    window: MainWindow, image_file: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    window.load_path(image_file)
    doc = window.document
    assert doc is not None
    monkeypatch.setattr("bluranything.core.faces.face_at", lambda *args, **kwargs: None)
    window._on_face_clicked(QPointF(10, 10))
    assert doc.is_empty


def test_gallery_holds_multiple_images(window: MainWindow, two_images: list[Path]) -> None:
    for path in two_images:
        window.load_path(path)
    assert len(window._items) == 2
    assert window._nav.count() == 2
    doc = window.document
    assert doc is not None
    assert doc.size == (34, 24)  # the second (last-loaded) image is current


def test_switching_images_preserves_edits(window: MainWindow, two_images: list[Path]) -> None:
    window.load_path(two_images[0])
    first = window.document
    assert first is not None
    first.stamp_rectangle((2, 2, 12, 12))
    window.editor.changed.emit()

    window.load_path(two_images[1])
    assert window.document is not None
    assert window.document.is_empty  # the new image starts clean

    window._select_item(0)
    assert window.document is first
    assert not first.is_empty  # the first image kept its edit


def test_remove_current_image(window: MainWindow, two_images: list[Path]) -> None:
    for path in two_images:
        window.load_path(path)
    window.remove_current()
    assert len(window._items) == 1
    assert window._nav.count() == 1
    assert window.document is not None


def test_removing_last_image_clears_editor(window: MainWindow, image_file: Path) -> None:
    window.load_path(image_file)
    window.remove_current()
    assert window.document is None
    assert window._nav.count() == 0


def test_export_all_writes_every_image(
    window: MainWindow, two_images: list[Path], tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    for path in two_images:
        window.load_path(path)
    out = tmp_path / "export"
    out.mkdir()
    monkeypatch.setattr(
        "bluranything.ui.main_window.QFileDialog.getExistingDirectory",
        lambda *args, **kwargs: str(out),
    )
    window._export_all()
    assert len(list(out.glob("*_blur.png"))) == 2


def test_drop_loads_image(window: MainWindow, tmp_path: Path) -> None:
    image = tmp_path / "drop.png"
    checkerboard((32, 24)).save(image)
    mime = QMimeData()
    mime.setUrls([QUrl.fromLocalFile(str(image))])
    event = QDropEvent(
        QPointF(5, 5),
        Qt.DropAction.CopyAction,
        mime,
        Qt.MouseButton.LeftButton,
        Qt.KeyboardModifier.NoModifier,
    )
    window.editor.dropEvent(event)
    doc = window.document
    assert doc is not None
    assert doc.size == (32, 24)


def test_copy_result_puts_image_on_clipboard(window: MainWindow, image_file: Path) -> None:
    window.load_path(image_file)
    doc = window.document
    assert doc is not None
    doc.stamp_rectangle((0, 0, 40, 30))
    window.editor.changed.emit()

    window.copy_result()
    out = image_from_clipboard()
    assert out is not None
    assert out.size == (40, 30)


def test_save_clears_autosave(window: MainWindow, image_file: Path, tmp_path: Path) -> None:
    window.load_path(image_file)
    doc = window.document
    assert doc is not None
    doc.stamp_rectangle((0, 0, 40, 30))
    window.editor.changed.emit()
    window._write_autosave()
    assert session.has_session(window._autosave_dir)

    window.save_to(tmp_path / "out.png")
    assert not session.has_session(window._autosave_dir)


def test_autosave_then_recover(
    qtbot: QtBot, tmp_path: Path, image_file: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    autosave_dir = tmp_path / "as"
    first = MainWindow(autosave_dir=autosave_dir)
    qtbot.addWidget(first, before_close_func=_reset_dirty)
    first.load_path(image_file)
    doc = first.document
    assert doc is not None
    doc.stamp_rectangle((5, 5, 25, 20))
    first.editor.changed.emit()
    first._write_autosave()
    assert session.has_session(autosave_dir)

    monkeypatch.setattr(
        "bluranything.ui.main_window.QMessageBox.question",
        lambda *args, **kwargs: QMessageBox.StandardButton.Yes,
    )
    recovered = MainWindow(autosave_dir=autosave_dir)
    qtbot.addWidget(recovered, before_close_func=_reset_dirty)
    assert recovered.document is not None
    assert not recovered.document.is_empty
    assert recovered.isWindowModified()


def test_recovery_declined_clears_session(
    qtbot: QtBot, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    autosave_dir = tmp_path / "as2"
    mask = new_mask((30, 20))
    stamp_rectangle(mask, (2, 2, 10, 10))
    session.save_session(
        autosave_dir,
        checkerboard((30, 20)),
        mask,
        effect_kind="blur",
        effect_value=10,
        edge_mode="soft",
        feather=6,
        source=None,
    )
    monkeypatch.setattr(
        "bluranything.ui.main_window.QMessageBox.question",
        lambda *args, **kwargs: QMessageBox.StandardButton.No,
    )
    window = MainWindow(autosave_dir=autosave_dir)
    qtbot.addWidget(window, before_close_func=_reset_dirty)
    assert window.document is None
    assert not session.has_session(autosave_dir)
