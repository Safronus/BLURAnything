"""GUI tests for the main window (offscreen)."""

from __future__ import annotations

from pathlib import Path

import pytest
from PIL import Image
from pytestqt.qtbot import QtBot

from bluranything.ui.main_window import MainWindow
from tests.helpers import checkerboard


def _reset_dirty(window: MainWindow) -> None:
    # Clear the dirty flag before qtbot closes the window at teardown, so the
    # confirm dialog never opens and blocks the headless run.
    window._dirty = False


@pytest.fixture
def window(qtbot: QtBot) -> MainWindow:
    win = MainWindow()
    qtbot.addWidget(win, before_close_func=_reset_dirty)
    return win


@pytest.fixture
def image_file(tmp_path: Path) -> Path:
    path = tmp_path / "input.png"
    checkerboard((40, 30)).save(path)
    return path


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
