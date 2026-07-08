"""Gaussian-blur operations on Pillow images."""

from __future__ import annotations

from PIL import Image, ImageFilter

DEFAULT_RADIUS = 12

#: (left, top, right, bottom) in pixel coordinates; right/bottom are exclusive.
Box = tuple[int, int, int, int]


def clamp_box(box: Box, size: tuple[int, int]) -> Box | None:
    """Normalize *box* and clamp it to an image of *size*.

    Swapped coordinates are reordered. Returns ``None`` when the clamped
    box has no area (fully outside the image or zero-sized).
    """
    width, height = size
    left, right = sorted((box[0], box[2]))
    top, bottom = sorted((box[1], box[3]))

    left = max(0, min(left, width))
    right = max(0, min(right, width))
    top = max(0, min(top, height))
    bottom = max(0, min(bottom, height))

    if right - left <= 0 or bottom - top <= 0:
        return None
    return (left, top, right, bottom)


def blur_region(image: Image.Image, box: Box, radius: int = DEFAULT_RADIUS) -> Image.Image:
    """Return a copy of *image* with *box* blurred by a Gaussian of *radius*.

    The box is clamped to the image bounds; a box without area yields an
    unchanged copy. Raises :class:`ValueError` for a non-positive radius.
    """
    if radius <= 0:
        msg = f"radius must be positive, got {radius}"
        raise ValueError(msg)

    result = image.copy()
    clamped = clamp_box(box, image.size)
    if clamped is None:
        return result

    region = result.crop(clamped).filter(ImageFilter.GaussianBlur(radius))
    result.paste(region, (clamped[0], clamped[1]))
    return result
