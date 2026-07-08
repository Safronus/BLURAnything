"""Tests for the pure blur core (no Qt required)."""

from __future__ import annotations

import pytest

from bluranything.core.blur import blur_region, clamp_box
from tests.helpers import checkerboard


def test_blur_changes_pixels_inside_box() -> None:
    image = checkerboard()
    result = blur_region(image, (4, 4, 20, 20), radius=3)
    assert result.crop((4, 4, 20, 20)).tobytes() != image.crop((4, 4, 20, 20)).tobytes()


def test_blur_keeps_pixels_outside_box() -> None:
    image = checkerboard()
    result = blur_region(image, (4, 4, 20, 20), radius=3)
    assert result.crop((20, 0, 32, 32)).tobytes() == image.crop((20, 0, 32, 32)).tobytes()
    assert result.crop((0, 20, 20, 32)).tobytes() == image.crop((0, 20, 20, 32)).tobytes()


def test_blur_does_not_mutate_original() -> None:
    image = checkerboard()
    before = image.tobytes()
    blur_region(image, (0, 0, 32, 32), radius=5)
    assert image.tobytes() == before


def test_blur_with_box_fully_outside_returns_unchanged_copy() -> None:
    image = checkerboard()
    result = blur_region(image, (100, 100, 200, 200), radius=5)
    assert result is not image
    assert result.tobytes() == image.tobytes()


def test_blur_clamps_box_partially_outside() -> None:
    image = checkerboard()
    result = blur_region(image, (-10, -10, 8, 8), radius=3)
    assert result.crop((0, 0, 8, 8)).tobytes() != image.crop((0, 0, 8, 8)).tobytes()
    assert result.crop((8, 8, 32, 32)).tobytes() == image.crop((8, 8, 32, 32)).tobytes()


@pytest.mark.parametrize("radius", [0, -1])
def test_blur_rejects_non_positive_radius(radius: int) -> None:
    with pytest.raises(ValueError, match="radius must be positive"):
        blur_region(checkerboard(), (0, 0, 8, 8), radius=radius)


def test_clamp_box_normalizes_swapped_coordinates() -> None:
    assert clamp_box((20, 20, 4, 4), (32, 32)) == (4, 4, 20, 20)


def test_clamp_box_returns_none_for_zero_area() -> None:
    assert clamp_box((5, 5, 5, 30), (32, 32)) is None
    assert clamp_box((40, 40, 50, 50), (32, 32)) is None
