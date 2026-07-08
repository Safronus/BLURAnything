"""Test helpers."""

from __future__ import annotations

from PIL import Image


def checkerboard(size: tuple[int, int] = (32, 32), tile: int = 1) -> Image.Image:
    """High-frequency checkerboard — any blur visibly changes it."""
    image = Image.new("RGBA", size)
    image.putdata(
        [
            (255, 255, 255, 255) if ((x // tile) + (y // tile)) % 2 else (0, 0, 0, 255)
            for y in range(size[1])
            for x in range(size[0])
        ]
    )
    return image
