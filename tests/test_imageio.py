"""Tests for image loading/saving, including HEIC and PDF."""

from __future__ import annotations

from pathlib import Path

import pytest
from PIL import Image

from bluranything.core import imageio
from tests.helpers import checkerboard


@pytest.mark.parametrize(
    "name", ["out.png", "out.tiff", "out.webp", "out.bmp", "out.jpg", "out.heic"]
)
def test_save_then_reload_preserves_size(tmp_path: Path, name: str) -> None:
    image = checkerboard((24, 18))
    path = tmp_path / name
    imageio.save(image, path)
    assert path.exists()
    reloaded = imageio.load(path)
    assert reloaded.size == image.size


def test_pdf_export_writes_a_file(tmp_path: Path) -> None:
    path = tmp_path / "out.pdf"
    imageio.save(checkerboard((20, 20)), path)
    assert path.stat().st_size > 0


def test_unsupported_format_raises(tmp_path: Path) -> None:
    with pytest.raises(ValueError, match="unsupported"):
        imageio.save(checkerboard((8, 8)), tmp_path / "out.gif")


def test_flatten_drops_alpha_onto_background() -> None:
    transparent = Image.new("RGBA", (4, 4), (255, 0, 0, 0))
    flat = imageio.flatten(transparent)
    assert flat.mode == "RGB"
    assert flat.getpixel((0, 0)) == (255, 255, 255)


def test_format_for_extension() -> None:
    assert imageio.format_for(Path("photo.PNG")) == "PNG"
    assert imageio.format_for(Path("photo.xyz")) is None
