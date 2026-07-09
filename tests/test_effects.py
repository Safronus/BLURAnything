"""Tests for redaction effects."""

from __future__ import annotations

from bluranything.core.effects import (
    GaussianBlurEffect,
    PixelateEffect,
    SolidFillEffect,
    effect_from,
)
from tests.helpers import checkerboard


def test_blur_changes_high_frequency_image() -> None:
    image = checkerboard((32, 32))
    out = GaussianBlurEffect(4).apply(image)
    assert out.size == image.size
    assert out.tobytes() != image.tobytes()


def test_zero_radius_is_a_noop_copy() -> None:
    image = checkerboard()
    out = GaussianBlurEffect(0).apply(image)
    assert out.tobytes() == image.tobytes()
    assert out is not image


def test_pixelate_changes_image_but_keeps_size() -> None:
    image = checkerboard((32, 32))
    out = PixelateEffect(8).apply(image)
    assert out.size == image.size
    assert out.tobytes() != image.tobytes()


def test_pixelate_block_one_is_a_noop_copy() -> None:
    image = checkerboard()
    out = PixelateEffect(1).apply(image)
    assert out.tobytes() == image.tobytes()
    assert out is not image


def test_solid_fill_replaces_every_pixel() -> None:
    out = SolidFillEffect((0, 0, 0, 255)).apply(checkerboard((10, 10)))
    assert out.size == (10, 10)
    assert out.getextrema() == ((0, 0), (0, 0), (0, 0), (255, 255))


def test_effects_compare_by_value() -> None:
    assert GaussianBlurEffect(5) == GaussianBlurEffect(5)
    assert GaussianBlurEffect(5) != GaussianBlurEffect(6)
    assert PixelateEffect(5) != PixelateEffect(9)


def test_effect_from_builds_by_key() -> None:
    assert isinstance(effect_from("blur", 5), GaussianBlurEffect)
    assert isinstance(effect_from("pixelate", 5), PixelateEffect)
    assert isinstance(effect_from("solid", 0), SolidFillEffect)
