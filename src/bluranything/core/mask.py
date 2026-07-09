"""Selection mask helpers.

A mask is an ``L`` (8-bit greyscale) image the same size as the document:
``0`` keeps the original pixel, ``255`` shows the redacted layer, values in
between blend the two. Tools stamp opaque (``255``) shapes into the mask;
:func:`feather` softens its edges for a natural look.
"""

from __future__ import annotations

from PIL import Image, ImageDraw, ImageFilter

MASK_MODE = "L"
OPAQUE = 255

#: (left, top, right, bottom) in pixel coordinates.
Box = tuple[float, float, float, float]


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


def feather(mask: Image.Image, radius: int) -> Image.Image:
    """Return a copy of *mask* with edges softened by a Gaussian of *radius*."""
    if radius <= 0:
        return mask.copy()
    return mask.filter(ImageFilter.GaussianBlur(radius))
