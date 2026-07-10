#!/usr/bin/env python3
"""Generate the BLURAnything application icon.

Draws a macOS-style rounded-square icon (blue gradient with three white bars,
the middle one blurred to evoke redaction) and exports every asset we need:

- ``assets/icon-1024.png`` — the master render
- ``assets/icon.ico`` — multi-size Windows icon
- ``assets/BLURAnything.icns`` — macOS icon (requires ``iconutil``, macOS only)
- ``src/bluranything/resources/icon.png`` — 512px icon bundled with the package

Run it after changing the design: ``.venv/bin/python assets/generate_icon.py``.
"""

from __future__ import annotations

import shutil
import subprocess
from pathlib import Path

from PIL import Image, ImageDraw, ImageFilter

ASSETS = Path(__file__).resolve().parent
REPO = ASSETS.parent
RESOURCES = REPO / "src" / "bluranything" / "resources"

MASTER = 1024
TOP = (42, 160, 255, 255)  # #2AA0FF
BOTTOM = (10, 90, 216, 255)  # #0A5AD8
BAR = (255, 255, 255, 240)

ICONSET_SIZES = {
    "icon_16x16.png": 16,
    "icon_16x16@2x.png": 32,
    "icon_32x32.png": 32,
    "icon_32x32@2x.png": 64,
    "icon_128x128.png": 128,
    "icon_128x128@2x.png": 256,
    "icon_256x256.png": 256,
    "icon_256x256@2x.png": 512,
    "icon_512x512.png": 512,
    "icon_512x512@2x.png": 1024,
}


def _gradient(size: int) -> Image.Image:
    column = Image.new("RGBA", (1, size))
    for y in range(size):
        t = y / (size - 1)
        pixel = tuple(round(a + (b - a) * t) for a, b in zip(TOP, BOTTOM, strict=True))
        column.putpixel((0, y), pixel)
    return column.resize((size, size))


def _rounded_alpha(size: int, radius: int) -> Image.Image:
    mask = Image.new("L", (size, size), 0)
    ImageDraw.Draw(mask).rounded_rectangle((0, 0, size - 1, size - 1), radius=radius, fill=255)
    return mask


def render_icon(size: int = MASTER) -> Image.Image:
    background = _gradient(size)
    background.putalpha(_rounded_alpha(size, round(size * 0.2237)))

    bars = Image.new("RGBA", (size, size), (0, 0, 0, 0))
    draw = ImageDraw.Draw(bars)
    left = round(size * 0.235)
    inner = size - 2 * left
    bar_h = round(size * 0.105)
    gap = round(size * 0.072)
    top = (size - (3 * bar_h + 2 * gap)) // 2
    rows: list[tuple[int, int]] = []
    for index, fraction in enumerate((0.90, 0.66, 0.78)):
        y0 = top + index * (bar_h + gap)
        rows.append((y0, y0 + bar_h))
        draw.rounded_rectangle(
            (left, y0, left + round(inner * fraction), y0 + bar_h),
            radius=bar_h // 2,
            fill=BAR,
        )

    # Blur the middle bar to signal redaction — this is what the app does.
    y0, y1 = rows[1]
    margin = round(gap * 0.45)
    band = (0, y0 - margin, size, y1 + margin)
    blurred = bars.crop(band).filter(ImageFilter.GaussianBlur(round(bar_h * 0.28)))
    bars.paste(blurred, (band[0], band[1]))

    return Image.alpha_composite(background, bars)


def main() -> None:
    master = render_icon()
    RESOURCES.mkdir(parents=True, exist_ok=True)

    master.save(ASSETS / "icon-1024.png")
    master.resize((512, 512), Image.Resampling.LANCZOS).save(RESOURCES / "icon.png")
    master.save(
        ASSETS / "icon.ico",
        sizes=[(16, 16), (32, 32), (48, 48), (64, 64), (128, 128), (256, 256)],
    )

    iconset = ASSETS / "icon.iconset"
    iconset.mkdir(exist_ok=True)
    for name, px in ICONSET_SIZES.items():
        master.resize((px, px), Image.Resampling.LANCZOS).save(iconset / name)

    iconutil = shutil.which("iconutil")
    if iconutil is not None:
        subprocess.run(
            [iconutil, "-c", "icns", str(iconset), "-o", str(ASSETS / "BLURAnything.icns")],
            check=True,
        )
        print("wrote", ASSETS / "BLURAnything.icns")
    else:
        print("iconutil not found; skipped .icns (macOS only)")
    print("wrote", ASSETS / "icon-1024.png", "and", RESOURCES / "icon.png")


if __name__ == "__main__":
    main()
