"""Tests for the non-destructive editing document."""

from __future__ import annotations

from bluranything.core.document import Document, EdgeMode
from bluranything.core.effects import GaussianBlurEffect
from bluranything.core.mask import new_mask
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


def test_ellipse_and_polygon_mark_nonempty() -> None:
    ellipse_doc = make_document()
    ellipse_doc.stamp_ellipse((5, 5, 20, 20))
    assert not ellipse_doc.is_empty

    polygon_doc = make_document()
    polygon_doc.stamp_polygon([(0, 0), (30, 0), (15, 20)])
    assert not polygon_doc.is_empty


def test_brush_stroke_collapses_into_one_undo_step() -> None:
    doc = make_document()
    doc.stamp_brush([(5, 5)], radius=4, new_stroke=True)
    doc.stamp_brush([(5, 5), (10, 5)], radius=4, new_stroke=False)
    doc.stamp_brush([(10, 5), (20, 5)], radius=4, new_stroke=False)
    assert not doc.is_empty
    doc.undo()
    assert doc.is_empty  # the whole stroke undoes at once


def test_stamp_faces_blurs_all_boxes_in_one_undo_step() -> None:
    doc = make_document()
    doc.stamp_faces([(2, 2, 15, 15), (20, 5, 35, 20)])
    assert not doc.is_empty
    doc.undo()
    assert doc.is_empty  # both faces collapse into a single step


def test_stamp_faces_with_no_boxes_is_noop() -> None:
    doc = make_document()
    doc.stamp_faces([])
    assert doc.is_empty
    assert not doc.can_undo


def test_clear_mask_is_undoable() -> None:
    doc = make_document()
    doc.stamp_rectangle((5, 5, 25, 20))
    doc.clear_mask()
    assert doc.is_empty
    assert doc.can_undo


def test_set_mask_replaces_and_clears_history() -> None:
    doc = make_document()
    doc.stamp_rectangle((5, 5, 20, 20))
    assert doc.can_undo
    doc.set_mask(new_mask(doc.size))
    assert doc.is_empty
    assert not doc.can_undo
