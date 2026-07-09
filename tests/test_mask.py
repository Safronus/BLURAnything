"""Tests for selection-mask helpers."""

from __future__ import annotations

from typing import cast

from bluranything.core.mask import (
    feather,
    new_mask,
    normalize_box,
    stamp_ellipse,
    stamp_polygon,
    stamp_rectangle,
    stamp_stroke,
)


def test_new_mask_is_empty() -> None:
    assert new_mask((10, 10)).getbbox() is None


def test_stamp_rectangle_fills_region() -> None:
    mask = new_mask((20, 20))
    stamp_rectangle(mask, (5, 5, 15, 15))
    assert mask.getpixel((10, 10)) == 255
    assert mask.getpixel((0, 0)) == 0


def test_stamp_ellipse_fills_center_not_corner() -> None:
    mask = new_mask((20, 20))
    stamp_ellipse(mask, (0, 0, 20, 20))
    assert cast(int, mask.getpixel((10, 10))) == 255
    assert cast(int, mask.getpixel((0, 0))) == 0


def test_stamp_polygon_fills_triangle() -> None:
    mask = new_mask((20, 20))
    stamp_polygon(mask, [(0, 0), (19, 0), (0, 19)])
    assert cast(int, mask.getpixel((2, 2))) == 255
    assert cast(int, mask.getpixel((18, 18))) == 0


def test_stamp_polygon_ignores_too_few_points() -> None:
    mask = new_mask((10, 10))
    stamp_polygon(mask, [(1, 1), (5, 5)])
    assert mask.getbbox() is None


def test_stamp_stroke_paints_along_path() -> None:
    mask = new_mask((40, 12))
    stamp_stroke(mask, [(5, 6), (35, 6)], radius=3)
    assert cast(int, mask.getpixel((20, 6))) == 255  # on the line
    assert cast(int, mask.getpixel((20, 0))) == 0  # well outside the radius


def test_normalize_box_orders_coordinates() -> None:
    assert normalize_box((15, 15, 5, 5)) == (5, 5, 15, 15)


def test_feather_softens_edges() -> None:
    mask = new_mask((30, 30))
    stamp_rectangle(mask, (10, 10, 20, 20))
    soft = feather(mask, 3)
    assert soft.getbbox() != mask.getbbox()  # blur spreads beyond the crisp edge
    core = cast(int, soft.getpixel((15, 15)))
    edge = cast(int, soft.getpixel((21, 15)))
    assert core > 150  # core stays strongly opaque
    assert 0 < edge < 255  # just outside the crisp edge is partial


def test_feather_zero_returns_copy() -> None:
    mask = new_mask((10, 10))
    stamp_rectangle(mask, (2, 2, 8, 8))
    out = feather(mask, 0)
    assert out.tobytes() == mask.tobytes()
    assert out is not mask
