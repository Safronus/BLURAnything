"""Tests for the non-destructive editing document."""

from __future__ import annotations

from bluranything.core.document import Document, EdgeMode
from bluranything.core.effects import GaussianBlurEffect
from tests.helpers import checkerboard


def make_document() -> Document:
    return Document(checkerboard((40, 30)))


def test_render_empty_returns_untouched_copy() -> None:
    doc = make_document()
    out = doc.render()
    assert doc.is_empty
    assert out.tobytes() == doc.base.tobytes()
    assert out is not doc.base


def test_stamp_marks_nonempty_and_changes_render() -> None:
    doc = make_document()
    doc.stamp_rectangle((5, 5, 25, 20))
    assert not doc.is_empty
    assert doc.render().tobytes() != doc.base.tobytes()


def test_undo_redo_roundtrip() -> None:
    doc = make_document()
    doc.stamp_rectangle((5, 5, 25, 20))
    assert doc.can_undo
    doc.undo()
    assert doc.is_empty
    assert doc.can_redo
    doc.redo()
    assert not doc.is_empty


def test_hard_edges_leave_outside_pixels_untouched() -> None:
    doc = make_document()
    doc.set_edge_mode(EdgeMode.HARD)
    doc.stamp_rectangle((5, 5, 25, 20))
    out = doc.render()
    assert out.crop((26, 0, 40, 30)).tobytes() == doc.base.crop((26, 0, 40, 30)).tobytes()


def test_soft_and_hard_edges_differ() -> None:
    doc = make_document()
    doc.stamp_rectangle((10, 10, 30, 25))
    doc.set_edge_mode(EdgeMode.HARD)
    hard = doc.render()
    doc.set_edge_mode(EdgeMode.SOFT)
    doc.set_feather(5)
    assert doc.render().tobytes() != hard.tobytes()


def test_changing_effect_changes_output() -> None:
    doc = make_document()
    doc.stamp_rectangle((5, 5, 35, 25))
    before = doc.render()
    doc.set_effect(GaussianBlurEffect(40))
    assert doc.render().tobytes() != before.tobytes()


def test_clear_mask_is_undoable() -> None:
    doc = make_document()
    doc.stamp_rectangle((5, 5, 25, 20))
    doc.clear_mask()
    assert doc.is_empty
    assert doc.can_undo
