"""Tests for selection-mask helpers."""

from __future__ import annotations

from bluranything.core.mask import feather, new_mask, normalize_box, stamp_rectangle


def test_new_mask_is_empty() -> None:
    assert new_mask((10, 10)).getbbox() is None


def test_stamp_rectangle_fills_region() -> None:
    mask = new_mask((20, 20))
    stamp_rectangle(mask, (5, 5, 15, 15))
    assert mask.getpixel((10, 10)) == 255
    assert mask.getpixel((0, 0)) == 0


def test_normalize_box_orders_coordinates() -> None:
    assert normalize_box((15, 15, 5, 5)) == (5, 5, 15, 15)


def test_feather_softens_edges() -> None:
    mask = new_mask((30, 30))
    stamp_rectangle(mask, (10, 10, 20, 20))
    soft = feather(mask, 3)
    assert soft.getbbox() != mask.getbbox()  # blur spreads beyond the crisp edge
    assert soft.getpixel((15, 15)) > 150  # core stays strongly opaque
    assert 0 < soft.getpixel((21, 15)) < 255  # just outside the edge is partial


def test_feather_zero_returns_copy() -> None:
    mask = new_mask((10, 10))
    stamp_rectangle(mask, (2, 2, 8, 8))
    out = feather(mask, 0)
    assert out.tobytes() == mask.tobytes()
    assert out is not mask
