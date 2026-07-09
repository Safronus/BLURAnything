"""Tests for the mask compositor."""

from __future__ import annotations

import pytest
from PIL import Image

from bluranything.core.compositor import composite


def test_composite_selects_layer_where_masked() -> None:
    base = Image.new("RGBA", (4, 4), (0, 0, 0, 255))
    layer = Image.new("RGBA", (4, 4), (255, 0, 0, 255))
    mask = Image.new("L", (4, 4), 0)
    mask.putpixel((1, 1), 255)

    out = composite(base, layer, mask)

    assert out.getpixel((1, 1)) == (255, 0, 0, 255)
    assert out.getpixel((0, 0)) == (0, 0, 0, 255)


def test_size_mismatch_raises() -> None:
    base = Image.new("RGBA", (4, 4))
    layer = Image.new("RGBA", (4, 4))
    mask = Image.new("L", (3, 3))
    with pytest.raises(ValueError, match="size mismatch"):
        composite(base, layer, mask)
