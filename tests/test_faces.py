"""Tests for offline face detection."""

from __future__ import annotations

import pytest
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


def test_face_at_selects_the_containing_face(monkeypatch: pytest.MonkeyPatch) -> None:
    from bluranything.core import faces

    boxes = [faces.FaceBox(10, 10, 20, 20), faces.FaceBox(50, 50, 30, 30)]
    monkeypatch.setattr(faces, "detect_faces", lambda *args, **kwargs: boxes)
    image = Image.new("RGB", (100, 100))

    inside = faces.face_at(image, (15, 15))
    assert inside is not None
    assert inside[0] <= 15 <= inside[2] and inside[1] <= 15 <= inside[3]
    assert faces.face_at(image, (5, 5)) is None  # not on any face
