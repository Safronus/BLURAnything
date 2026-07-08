"""Tests for application bootstrap and CLI arguments."""

from __future__ import annotations

from pathlib import Path

import pytest
from PySide6.QtWidgets import QApplication

from bluranything import __version__
from bluranything.app import main, parse_args
from tests.helpers import checkerboard


def test_version_flag_exits_cleanly(capsys: pytest.CaptureFixture[str]) -> None:
    with pytest.raises(SystemExit) as excinfo:
        parse_args(["--version"])
    assert excinfo.value.code == 0
    assert __version__ in capsys.readouterr().out


def test_parse_args_accepts_optional_image() -> None:
    assert parse_args([]).image is None
    assert parse_args(["photo.png"]).image == Path("photo.png")


def test_main_boots_with_image(
    qapp: QApplication, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    image_file = tmp_path / "input.png"
    checkerboard((20, 20)).save(image_file)

    # Don't spin the real event loop; everything up to exec() runs for real.
    monkeypatch.setattr(QApplication, "exec", lambda *args: 0)

    assert main([str(image_file)]) == 0
    assert qapp.applicationName() == "BLURAnything"
    assert qapp.applicationVersion() == __version__
