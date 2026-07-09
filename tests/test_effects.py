"""Tests for redaction effects."""

from __future__ import annotations

from bluranything.core.effects import GaussianBlurEffect
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


def test_effects_compare_by_value() -> None:
    assert GaussianBlurEffect(5) == GaussianBlurEffect(5)
    assert GaussianBlurEffect(5) != GaussianBlurEffect(6)
