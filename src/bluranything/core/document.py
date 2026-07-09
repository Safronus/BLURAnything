"""The non-destructive editing document.

A :class:`Document` owns the original image plus a selection mask and the
current effect. It never mutates the original: :meth:`render` composites a
fresh result on demand. All state lives here (Qt-free) so the whole editing
model is unit-testable without a GUI.
"""

from __future__ import annotations

from collections.abc import Sequence
from enum import Enum

from PIL import Image

from bluranything.core import mask as mask_ops
from bluranything.core.compositor import composite
from bluranything.core.effects import Effect, GaussianBlurEffect

DEFAULT_FEATHER = 6
MAX_HISTORY = 30


class EdgeMode(Enum):
    """How the boundary of a redacted region looks."""

    SOFT = "soft"  # feathered, blends into the surroundings
    HARD = "hard"  # crisp edge, like a censor bar


class Document:
    """Original image + selection mask + effect, rendered non-destructively."""

    def __init__(self, base: Image.Image, effect: Effect | None = None) -> None:
        self.base = base.convert("RGBA")
        self._mask = mask_ops.new_mask(self.base.size)
        self._effect: Effect = effect or GaussianBlurEffect()
        self._edge = EdgeMode.SOFT
        self._feather = DEFAULT_FEATHER
        self._layer_cache: Image.Image | None = None
        self._undo: list[bytes] = []
        self._redo: list[bytes] = []

    # --------------------------------------------------------------- settings

    @property
    def size(self) -> tuple[int, int]:
        return self.base.size

    @property
    def effect(self) -> Effect:
        return self._effect

    def set_effect(self, effect: Effect) -> None:
        if effect != self._effect:
            self._effect = effect
            self._layer_cache = None  # parameters changed, recompute the layer

    @property
    def edge_mode(self) -> EdgeMode:
        return self._edge

    def set_edge_mode(self, mode: EdgeMode) -> None:
        self._edge = mode

    @property
    def feather(self) -> int:
        return self._feather

    def set_feather(self, radius: int) -> None:
        self._feather = max(0, radius)

    # ------------------------------------------------------------ mask edits

    @property
    def is_empty(self) -> bool:
        """True while nothing has been redacted yet."""
        return self._mask.getbbox() is None

    def mask_copy(self) -> Image.Image:
        """A copy of the raw (unfeathered) mask, e.g. for an editor overlay."""
        return self._mask.copy()

    def set_mask(self, mask: Image.Image) -> None:
        """Replace the whole selection mask (for session restore; clears history)."""
        if mask.size != self.base.size:
            msg = f"mask size {mask.size} does not match image {self.base.size}"
            raise ValueError(msg)
        self._mask = mask.convert(mask_ops.MASK_MODE)
        self._undo.clear()
        self._redo.clear()

    def stamp_rectangle(self, box: mask_ops.Box, *, new_stroke: bool = True) -> None:
        """Add a rectangle to the selection. Groups into one undo step per stroke."""
        if new_stroke:
            self._begin_change()
        mask_ops.stamp_rectangle(self._mask, box)

    def stamp_ellipse(self, box: mask_ops.Box, *, new_stroke: bool = True) -> None:
        """Add an ellipse (bounded by *box*) to the selection."""
        if new_stroke:
            self._begin_change()
        mask_ops.stamp_ellipse(self._mask, box)

    def stamp_polygon(self, points: Sequence[mask_ops.Point], *, new_stroke: bool = True) -> None:
        """Add a polygon through *points* to the selection."""
        if new_stroke:
            self._begin_change()
        mask_ops.stamp_polygon(self._mask, points)

    def stamp_brush(
        self, points: Sequence[mask_ops.Point], radius: int, *, new_stroke: bool = True
    ) -> None:
        """Paint a brush stroke of *radius* through *points*.

        Pass ``new_stroke=True`` for the first dab of a drag and ``False`` for
        the rest, so the whole stroke collapses into a single undo step.
        """
        if new_stroke:
            self._begin_change()
        mask_ops.stamp_stroke(self._mask, points, radius)

    def clear_mask(self) -> None:
        """Remove all redactions (undoable)."""
        if self.is_empty:
            return
        self._begin_change()
        self._mask = mask_ops.new_mask(self.base.size)

    # --------------------------------------------------------------- history

    def _begin_change(self) -> None:
        """Snapshot the mask before a new edit, enabling undo."""
        self._undo.append(self._mask.tobytes())
        del self._undo[:-MAX_HISTORY]
        self._redo.clear()

    @property
    def can_undo(self) -> bool:
        return bool(self._undo)

    @property
    def can_redo(self) -> bool:
        return bool(self._redo)

    def undo(self) -> None:
        if self._undo:
            self._redo.append(self._mask.tobytes())
            self._mask = self._mask_from_bytes(self._undo.pop())

    def redo(self) -> None:
        if self._redo:
            self._undo.append(self._mask.tobytes())
            self._mask = self._mask_from_bytes(self._redo.pop())

    def _mask_from_bytes(self, data: bytes) -> Image.Image:
        return Image.frombytes(mask_ops.MASK_MODE, self.base.size, data)

    # --------------------------------------------------------------- render

    def _effect_layer(self) -> Image.Image:
        if self._layer_cache is None:
            self._layer_cache = self._effect.apply(self.base)
        return self._layer_cache

    def _render_mask(self) -> Image.Image:
        if self._edge is EdgeMode.HARD:
            return self._mask
        return mask_ops.feather(self._mask, self._feather)

    def render(self) -> Image.Image:
        """Composite the current result. Returns the original when nothing is masked."""
        if self.is_empty:
            return self.base.copy()
        return composite(self.base, self._effect_layer(), self._render_mask())
