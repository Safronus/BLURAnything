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
