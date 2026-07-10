"""Tests for offline face detection."""

from __future__ import annotations

from PIL import Image

from bluranything.core.faces import FaceBox, detect_faces, face_boxes


def test_facebox_expanded_grows_and_clamps() -> None:
    face = FaceBox(10, 10, 20, 20)
    assert face.expanded(0.5, (100, 100)) == (0, 0, 40, 40)  # +50% each side, clamped at 0

    near_edge = FaceBox(90, 90, 20, 20)
    assert near_edge.expanded(0.5, (100, 100)) == (80, 80, 100, 100)  # clamped to image


def test_detect_blank_image_finds_no_faces() -> None:
    blank = Image.new("RGB", (200, 160), (127, 127, 127))
    assert detect_faces(blank, backend="yunet") == []
    assert detect_faces(blank, backend="haar") == []
    assert face_boxes(blank) == []
