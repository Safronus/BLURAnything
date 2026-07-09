"""Selection mask helpers.

A mask is an ``L`` (8-bit greyscale) image the same size as the document:
``0`` keeps the original pixel, ``255`` shows the redacted layer, values in
between blend the two. Tools stamp opaque (``255``) shapes into the mask;
:func:`feather` softens its edges for a natural look.
"""

from __future__ import annotations

from collections.abc import Sequence

from PIL import Image, ImageDraw, ImageFilter

MASK_MODE = "L"
OPAQUE = 255

#: (left, top, right, bottom) in pixel coordinates.
Box = tuple[float, float, float, float]
#: A point in pixel coordinates.
Point = tuple[float, float]


def _ipoints(points: Sequence[Point]) -> list[tuple[int, int]]:
    return [(round(x), round(y)) for x, y in points]


def new_mask(size: tuple[int, int]) -> Image.Image:
    """An empty (fully transparent) mask of *size*."""
    return Image.new(MASK_MODE, size, 0)


def normalize_box(box: Box) -> tuple[int, int, int, int]:
    """Reorder *box* to (left, top, right, bottom) with integer coordinates."""
    left, right = sorted((box[0], box[2]))
    top, bottom = sorted((box[1], box[3]))
    return round(left), round(top), round(right), round(bottom)


def stamp_rectangle(mask: Image.Image, box: Box) -> None:
    """Fill the rectangle *box* into *mask* (in place)."""
    ImageDraw.Draw(mask).rectangle(normalize_box(box), fill=OPAQUE)


def stamp_ellipse(mask: Image.Image, box: Box) -> None:
    """Fill the ellipse bounded by *box* into *mask* (in place)."""
    ImageDraw.Draw(mask).ellipse(normalize_box(box), fill=OPAQUE)


def stamp_polygon(mask: Image.Image, points: Sequence[Point]) -> None:
    """Fill the polygon through *points* into *mask*; needs at least 3 points."""
    pixels = _ipoints(points)
    if len(pixels) >= 3:
        ImageDraw.Draw(mask).polygon(pixels, fill=OPAQUE)


def stamp_stroke(mask: Image.Image, points: Sequence[Point], radius: int) -> None:
    """Paint a round brush stroke of *radius* through *points* into *mask*."""
    draw = ImageDraw.Draw(mask)
    pixels = _ipoints(points)
    diameter = 2 * max(1, radius)
    if len(pixels) >= 2:
        draw.line(pixels, fill=OPAQUE, width=diameter, joint="curve")
    for x, y in pixels:  # round every cap and joint
        draw.ellipse((x - radius, y - radius, x + radius, y + radius), fill=OPAQUE)


def feather(mask: Image.Image, radius: int) -> Image.Image:
    """Return a copy of *mask* with edges softened by a Gaussian of *radius*."""
    if radius <= 0:
        return mask.copy()
    return mask.filter(ImageFilter.GaussianBlur(radius))
