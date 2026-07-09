"""Tests for session persistence (crash/close recovery)."""

from __future__ import annotations

from pathlib import Path

from bluranything.core.mask import new_mask, stamp_rectangle
from bluranything.core.session import (
    clear_session,
    has_session,
    load_session,
    save_session,
)
from tests.helpers import checkerboard


def test_session_roundtrip(tmp_path: Path) -> None:
    base = checkerboard((20, 16))
    mask = new_mask((20, 16))
    stamp_rectangle(mask, (2, 2, 10, 10))

    save_session(
        tmp_path,
        base,
        mask,
        effect_kind="pixelate",
        effect_value=8,
        edge_mode="hard",
        feather=3,
        source="/x/y.png",
    )
    assert has_session(tmp_path)

    restored = load_session(tmp_path)
    assert restored is not None
    assert restored.base.size == (20, 16)
    # ImageDraw fills the right/bottom edge inclusively, so bbox is one past 10.
    assert restored.mask.getbbox() == (2, 2, 11, 11)
    assert restored.effect_kind == "pixelate"
    assert restored.effect_value == 8
    assert restored.edge_mode == "hard"
    assert restored.feather == 3
    assert restored.source == "/x/y.png"

    clear_session(tmp_path)
    assert not has_session(tmp_path)
    assert load_session(tmp_path) is None


def test_load_missing_returns_none(tmp_path: Path) -> None:
    assert load_session(tmp_path / "nothing") is None
