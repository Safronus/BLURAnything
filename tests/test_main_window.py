"""GUI tests for the main window (offscreen)."""

from __future__ import annotations

from pathlib import Path

import pytest
from PIL import Image
from PySide6.QtCore import QRect
from pytestqt.qtbot import QtBot

from bluranything.ui.main_window import MainWindow
from tests.helpers import checkerboard


@pytest.fixture
def window(qtbot: QtBot) -> MainWindow:
    win = MainWindow()
    # Clear the modified flag before qtbot closes the window at teardown —
    # otherwise closeEvent opens a confirm dialog and blocks the headless run.
    qtbot.addWidget(win, before_close_func=lambda w: w.setWindowModified(False))
    return win


@pytest.fixture
def image_file(tmp_path: Path) -> Path:
    path = tmp_path / "input.png"
    checkerboard((40, 30)).save(path)
    return path


def test_initial_state_has_no_image(window: MainWindow) -> None:
    assert window.image is None
    assert not window._save_action.isEnabled()
    assert not window._undo_action.isEnabled()
    assert "BLURAnything" in window.windowTitle()


def test_load_image_enables_editing(window: MainWindow, image_file: Path) -> None:
    assert window.load_image(image_file)
    assert window.image is not None
    assert window.image.size == (40, 30)
    assert window._save_action.isEnabled()
    assert not window.isWindowModified()
    assert image_file.name in window.windowTitle()


def test_load_missing_file_reports_error(
    window: MainWindow, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    errors: list[str] = []
    monkeypatch.setattr(
        "bluranything.ui.main_window.QMessageBox.critical",
        lambda *args: errors.append(str(args[2])),
    )
    assert not window.load_image(tmp_path / "missing.png")
    assert window.image is None
    assert len(errors) == 1


def test_apply_blur_marks_dirty_and_changes_image(window: MainWindow, image_file: Path) -> None:
    window.load_image(image_file)
    assert window.image is not None
    before = window.image.tobytes()

    window.apply_blur(QRect(5, 5, 20, 15))

    assert window.image is not None
    assert window.image.tobytes() != before
    assert window.isWindowModified()
    assert window._undo_action.isEnabled()


def test_undo_restores_previous_image(window: MainWindow, image_file: Path) -> None:
    window.load_image(image_file)
    assert window.image is not None
    before = window.image.tobytes()

    window.apply_blur(QRect(5, 5, 20, 15))
    window.undo()

    assert window.image is not None
    assert window.image.tobytes() == before
    assert not window._undo_action.isEnabled()


def test_save_to_writes_blurred_file(window: MainWindow, image_file: Path, tmp_path: Path) -> None:
    window.load_image(image_file)
    window.apply_blur(QRect(0, 0, 40, 30))

    out = tmp_path / "output.png"
    assert window.save_to(out)
    assert not window.isWindowModified()

    with Image.open(out) as saved:
        assert saved.size == (40, 30)
        assert saved.convert("RGBA").tobytes() != checkerboard((40, 30)).tobytes()


def test_save_to_jpeg_drops_alpha(window: MainWindow, image_file: Path, tmp_path: Path) -> None:
    window.load_image(image_file)
    out = tmp_path / "output.jpg"
    assert window.save_to(out)
    with Image.open(out) as saved:
        assert saved.mode == "RGB"
