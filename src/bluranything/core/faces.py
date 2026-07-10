"""Offline face detection with OpenCV.

Two selectable backends, both fully local (no network, privacy-safe):

- ``YUNET`` — a small bundled ONNX model (accurate, handles some angles).
- ``HAAR`` — OpenCV's built-in frontal-face cascade (faster, less robust).

This module is Qt-free. OpenCV/NumPy are imported at module load, so import it
lazily from the UI to keep application start-up snappy.
"""

from __future__ import annotations

from dataclasses import dataclass
from importlib import resources
from pathlib import Path
from typing import Any

import cv2
import numpy as np
from PIL import Image

YUNET = "yunet"
HAAR = "haar"

DEFAULT_BACKEND = YUNET
DEFAULT_SENSITIVITY = 0.5
DEFAULT_MARGIN = 0.18

_YUNET_FILE = "face_detection_yunet_2023mar.onnx"
_HAAR_FILE = "haarcascade_frontalface_default.xml"

#: (left, top, right, bottom) box in pixel coordinates.
Box = tuple[int, int, int, int]


@dataclass(frozen=True)
class FaceBox:
    """A detected face as an x/y/width/height rectangle."""

    left: int
    top: int
    width: int
    height: int

    def expanded(self, margin: float, size: tuple[int, int]) -> Box:
        """Grow the box by *margin* (fraction of its size), clamped to *size*."""
        image_w, image_h = size
        dx = self.width * margin
        dy = self.height * margin
        left = max(0, round(self.left - dx))
        top = max(0, round(self.top - dy))
        right = min(image_w, round(self.left + self.width + dx))
        bottom = min(image_h, round(self.top + self.height + dy))
        return (left, top, right, bottom)


def _clamp(value: float, low: float, high: float) -> float:
    return max(low, min(high, value))


def _yunet_model_path() -> Path:
    return Path(str(resources.files("bluranything.resources") / _YUNET_FILE))


def _to_bgr(image: Image.Image) -> Any:
    rgb = np.asarray(image.convert("RGB"))
    return np.ascontiguousarray(rgb[:, :, ::-1])  # RGB -> BGR for OpenCV


def _detect_yunet(bgr: Any, sensitivity: float) -> list[FaceBox]:
    height, width = bgr.shape[:2]
    score = _clamp(0.9 - sensitivity * 0.6, 0.1, 0.9)  # more sensitive -> lower threshold
    detector = cv2.FaceDetectorYN.create(
        str(_yunet_model_path()), "", (width, height), score, 0.3, 5000
    )
    detector.setInputSize((width, height))
    _, faces = detector.detect(bgr)
    if faces is None:
        return []
    return [FaceBox(int(f[0]), int(f[1]), int(f[2]), int(f[3])) for f in faces]


def _detect_haar(bgr: Any, sensitivity: float) -> list[FaceBox]:
    gray = cv2.cvtColor(bgr, cv2.COLOR_BGR2GRAY)
    haar_dir = cv2.data.haarcascades  # type: ignore[attr-defined]  # missing from OpenCV stubs
    cascade = cv2.CascadeClassifier(haar_dir + _HAAR_FILE)
    neighbors = round(2 + (1.0 - sensitivity) * 8)  # more sensitive -> fewer neighbours
    rects = cascade.detectMultiScale(
        gray, scaleFactor=1.1, minNeighbors=neighbors, minSize=(24, 24)
    )
    return [FaceBox(int(x), int(y), int(w), int(h)) for x, y, w, h in rects]


def detect_faces(
    image: Image.Image,
    *,
    backend: str = DEFAULT_BACKEND,
    sensitivity: float = DEFAULT_SENSITIVITY,
) -> list[FaceBox]:
    """Detect faces in *image*. Higher *sensitivity* (0-1) finds more faces."""
    bgr = _to_bgr(image)
    if backend == HAAR:
        return _detect_haar(bgr, sensitivity)
    return _detect_yunet(bgr, sensitivity)


def face_boxes(
    image: Image.Image,
    *,
    backend: str = DEFAULT_BACKEND,
    sensitivity: float = DEFAULT_SENSITIVITY,
    margin: float = DEFAULT_MARGIN,
) -> list[Box]:
    """Detected faces as expanded (left, top, right, bottom) boxes ready to blur."""
    faces = detect_faces(image, backend=backend, sensitivity=sensitivity)
    return [face.expanded(margin, image.size) for face in faces]


def face_at(
    image: Image.Image,
    point: tuple[float, float],
    *,
    backend: str = DEFAULT_BACKEND,
    sensitivity: float = DEFAULT_SENSITIVITY,
    margin: float = DEFAULT_MARGIN,
) -> Box | None:
    """The expanded box of the face under *point*, or None if none is there."""
    px, py = point
    hits = [
        face
        for face in detect_faces(image, backend=backend, sensitivity=sensitivity)
        if face.left <= px <= face.left + face.width and face.top <= py <= face.top + face.height
    ]
    if not hits:
        return None
    smallest = min(hits, key=lambda face: face.width * face.height)
    return smallest.expanded(margin, image.size)
