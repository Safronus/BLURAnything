"""Blend a redacted layer onto the original through a mask."""

from __future__ import annotations

from PIL import Image


def composite(base: Image.Image, layer: Image.Image, mask: Image.Image) -> Image.Image:
    """Combine *base* and *layer* using *mask*.

    Where *mask* is ``255`` the result shows *layer* (the redacted pixels),
    where it is ``0`` it shows *base*; intermediate values blend the two.
    All three images must share the same size.
    """
    if not (base.size == layer.size == mask.size):
        msg = f"size mismatch: base={base.size} layer={layer.size} mask={mask.size}"
        raise ValueError(msg)
    return Image.composite(layer.convert("RGBA"), base.convert("RGBA"), mask)
