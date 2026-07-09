"""Redaction effects.

An :class:`Effect` turns a whole image into a "redacted layer" of the same
size. The :mod:`~bluranything.core.compositor` then blends that layer back onto
the original through a mask, so only the masked regions are affected.

Effects are frozen dataclasses: they are cheap value objects with equality, so
the document can detect parameter changes and cache the rendered layer.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Protocol, runtime_checkable

from PIL import Image, ImageFilter

DEFAULT_BLUR_RADIUS = 12
DEFAULT_PIXEL_SIZE = 12
DEFAULT_FILL_COLOR = (0, 0, 0, 255)


@runtime_checkable
class Effect(Protocol):
    """Produces a fully-redacted copy of an image."""

    def apply(self, image: Image.Image) -> Image.Image: ...


@dataclass(frozen=True)
class GaussianBlurEffect:
    """Soft Gaussian blur; larger *radius* means blurrier."""

    radius: int = DEFAULT_BLUR_RADIUS

    def apply(self, image: Image.Image) -> Image.Image:
        if self.radius <= 0:
            return image.copy()
        return image.filter(ImageFilter.GaussianBlur(self.radius))


@dataclass(frozen=True)
class PixelateEffect:
    """Mosaic / pixelation; larger *block* means coarser blocks."""

    block: int = DEFAULT_PIXEL_SIZE

    def apply(self, image: Image.Image) -> Image.Image:
        if self.block <= 1:
            return image.copy()
        width, height = image.size
        small = image.resize(
            (max(1, width // self.block), max(1, height // self.block)),
            Image.Resampling.BILINEAR,
        )
        return small.resize((width, height), Image.Resampling.NEAREST)


@dataclass(frozen=True)
class SolidFillEffect:
    """Opaque fill — the strongest, irreversible redaction (a censor bar)."""

    color: tuple[int, int, int, int] = DEFAULT_FILL_COLOR

    def apply(self, image: Image.Image) -> Image.Image:
        return Image.new("RGBA", image.size, self.color)
