"""Persist an in-progress editing session for crash/close recovery.

A session is a small directory holding the original image, the selection mask
and a JSON sidecar with the current effect and edge settings. This is Qt-free
so it can be unit-tested directly.
"""

from __future__ import annotations

import json
import shutil
from dataclasses import dataclass
from pathlib import Path

from PIL import Image

_META = "session.json"
_BASE = "base.png"
_MASK = "mask.png"


@dataclass(frozen=True)
class RestoredSession:
    """A session read back from disk."""

    base: Image.Image
    mask: Image.Image
    effect_kind: str
    effect_value: int
    edge_mode: str
    feather: int
    source: str | None


def save_session(
    directory: Path,
    base: Image.Image,
    mask: Image.Image,
    *,
    effect_kind: str,
    effect_value: int,
    edge_mode: str,
    feather: int,
    source: str | None,
) -> None:
    """Write the working state to *directory* (created if missing)."""
    directory.mkdir(parents=True, exist_ok=True)
    base.save(directory / _BASE)
    mask.save(directory / _MASK)
    meta = {
        "effect_kind": effect_kind,
        "effect_value": effect_value,
        "edge_mode": edge_mode,
        "feather": feather,
        "source": source,
    }
    (directory / _META).write_text(json.dumps(meta), encoding="utf-8")


def has_session(directory: Path) -> bool:
    """True when *directory* holds a complete session."""
    return all((directory / name).exists() for name in (_META, _BASE, _MASK))


def load_session(directory: Path) -> RestoredSession | None:
    """Read the session from *directory*, or None when there is none."""
    if not has_session(directory):
        return None
    meta = json.loads((directory / _META).read_text(encoding="utf-8"))
    with Image.open(directory / _BASE) as base_file:
        base = base_file.convert("RGBA")
    with Image.open(directory / _MASK) as mask_file:
        mask = mask_file.convert("L")
    return RestoredSession(
        base=base,
        mask=mask,
        effect_kind=str(meta["effect_kind"]),
        effect_value=int(meta["effect_value"]),
        edge_mode=str(meta["edge_mode"]),
        feather=int(meta["feather"]),
        source=meta["source"],
    )


def clear_session(directory: Path) -> None:
    """Delete the session directory if present."""
    shutil.rmtree(directory, ignore_errors=True)
