#!/usr/bin/env python3
"""Generate the BLURAnything application icon.

Draws a macOS-style rounded-square icon: a friendly cartoon face on a blue
gradient, whose right half progressively blurs and melts away — exactly what
the app does to faces. Exports every asset we need:

- ``assets/icon-1024.png`` — the master render
- ``assets/icon.ico`` — multi-size Windows icon
- ``assets/BLURAnything.icns`` — macOS icon (requires ``iconutil``, macOS only)
- ``src/bluranything/resources/icon.png`` — 512px icon bundled with the package

Run it after changing the design: ``.venv/bin/python assets/generate_icon.py``.
"""

from __future__ import annotations

import math
import shutil
import subprocess
from pathlib import Path

from PIL import Image, ImageChops, ImageDraw, ImageFilter

ASSETS = Path(__file__).resolve().parent
REPO = ASSETS.parent
RESOURCES = REPO / "src" / "bluranything" / "resources"

MASTER = 1024
SUPERSAMPLE = 2  # draw larger, then downscale for smooth anti-aliased edges
CORNER = 0.2237  # macOS squircle corner radius as a fraction of the icon size

TOP = (42, 160, 255, 255)  # #2AA0FF
BOTTOM = (10, 90, 216, 255)  # #0A5AD8
SKIN = (255, 218, 179, 255)
HAIR = (60, 46, 44, 255)
EYE_WHITE = (255, 255, 255, 255)
PUPIL = (54, 44, 60, 255)
CHEEK = (255, 120, 130, 160)
MOUTH = (150, 70, 74, 255)

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


def _horizontal_ramp(size: int, start: float, end: float) -> Image.Image:
    """Left-to-right 0→255 ramp: 0 left of *start*, 255 right of *end* (fractions)."""
    row = Image.new("L", (size, 1))
    x0, x1 = size * start, size * end
    for x in range(size):
        if x <= x0:
            value = 0
        elif x >= x1:
            value = 255
        else:
            value = round((x - x0) / (x1 - x0) * 255)
        row.putpixel((x, 0), value)
    return row.resize((size, size))


def _draw_character(size: int) -> Image.Image:
    """A cute cartoon face on a transparent layer."""
    layer = Image.new("RGBA", (size, size), (0, 0, 0, 0))
    draw = ImageDraw.Draw(layer)

    def box(cx: float, cy: float, rx: float, ry: float) -> tuple[float, float, float, float]:
        return (cx - rx, cy - ry, cx + rx, cy + ry)

    cx = size * 0.5
    cy = size * 0.55
    face_r = size * 0.30

    # ears
    for sign in (-1, 1):
        draw.ellipse(
            box(cx + sign * face_r * 0.94, cy + size * 0.02, size * 0.06, size * 0.07), fill=SKIN
        )
    # face
    draw.ellipse(box(cx, cy, face_r, face_r * 1.05), fill=SKIN)
    # hair: a crescent framing the top, plus a soft fringe of overlapping tufts
    draw.ellipse(box(cx, cy - face_r * 0.34, face_r * 1.02, face_r * 0.98), fill=HAIR)
    draw.ellipse(box(cx, cy - face_r * 0.02, face_r * 0.98, face_r * 1.02), fill=SKIN)
    for i in range(-2, 3):
        tuft_x = cx + i * face_r * 0.42
        draw.ellipse(box(tuft_x, cy - face_r * 0.66, face_r * 0.30, face_r * 0.26), fill=HAIR)

    eye_dx = size * 0.115
    eye_y = cy - size * 0.015
    for sign in (-1, 1):
        ex = cx + sign * eye_dx
        draw.ellipse(box(ex, eye_y, size * 0.056, size * 0.070), fill=EYE_WHITE)
        draw.ellipse(
            box(ex + sign * size * 0.006, eye_y + size * 0.012, size * 0.032, size * 0.036),
            fill=PUPIL,
        )
        draw.ellipse(
            box(ex - size * 0.012, eye_y - size * 0.012, size * 0.012, size * 0.012), fill=EYE_WHITE
        )
        # eyebrow
        draw.arc(
            box(ex, eye_y - size * 0.085, size * 0.060, size * 0.045),
            200,
            340,
            fill=HAIR,
            width=round(size * 0.013),
        )

    # cheeks — soft blush composited over the skin (not straight onto the layer,
    # or the semi-transparent pink would later blend with the blue background)
    blush = Image.new("RGBA", (size, size), (0, 0, 0, 0))
    blush_draw = ImageDraw.Draw(blush)
    for sign in (-1, 1):
        blush_draw.ellipse(
            box(cx + sign * size * 0.155, cy + size * 0.088, size * 0.055, size * 0.040), fill=CHEEK
        )
    blush = blush.filter(ImageFilter.GaussianBlur(round(size * 0.010)))
    layer = Image.alpha_composite(layer, blush)
    draw = ImageDraw.Draw(layer)

    # smile (arc with rounded ends)
    mcx, mcy = cx, cy + size * 0.075
    mrx, mry = size * 0.105, size * 0.095
    width = round(size * 0.020)
    draw.arc((mcx - mrx, mcy - mry, mcx + mrx, mcy + mry), 25, 155, fill=MOUTH, width=width)
    for angle in (25, 155):
        px = mcx + mrx * math.cos(math.radians(angle))
        py = mcy + mry * math.sin(math.radians(angle))
        draw.ellipse(box(px, py, width / 2, width / 2), fill=MOUTH)

    return layer


def _compose(size: int) -> Image.Image:
    rounded = _rounded_alpha(size, round(size * CORNER))
    background = _gradient(size)
    background.putalpha(rounded)

    character = _draw_character(size)
    blurred = character.filter(ImageFilter.GaussianBlur(round(size * 0.045)))
    # Left half stays sharp, right half blurs — with a visible transition band.
    face = Image.composite(blurred, character, _horizontal_ramp(size, 0.44, 0.82))

    # Let the blurred side melt a touch into the background, and clip to the squircle.
    fade = _horizontal_ramp(size, 0.82, 1.0).point(lambda v: 255 - round(v * 0.30))
    alpha = ImageChops.multiply(ImageChops.multiply(face.getchannel("A"), fade), rounded)
    face.putalpha(alpha)

    return Image.alpha_composite(background, face)


def render_icon(size: int = MASTER) -> Image.Image:
    big = _compose(size * SUPERSAMPLE)
    return big.resize((size, size), Image.Resampling.LANCZOS)


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
