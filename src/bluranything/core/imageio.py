"""Loading and saving images, including HEIC and PDF.

Pillow gains HEIC/HEIF support once :func:`register` has run (via
``pillow-heif``). All other formats are handled by Pillow directly.
"""

from __future__ import annotations

from pathlib import Path

from PIL import Image
from pillow_heif import register_heif_opener

#: Extensions accepted for opening — "blur anything".
INPUT_EXTENSIONS = (".png", ".tif", ".tiff", ".jpg", ".jpeg", ".heic", ".heif", ".bmp", ".webp")

#: Pillow format name per extension for saving.
_SAVE_FORMATS = {
    ".png": "PNG",
    ".tif": "TIFF",
    ".tiff": "TIFF",
    ".jpg": "JPEG",
    ".jpeg": "JPEG",
    ".heic": "HEIF",
    ".heif": "HEIF",
    ".bmp": "BMP",
    ".webp": "WEBP",
    ".pdf": "PDF",
}

#: Formats that cannot store alpha and must be flattened first.
_NO_ALPHA = {"JPEG", "BMP", "PDF"}

_FLATTEN_BACKGROUND = (255, 255, 255)

_registered = False


def register() -> None:
    """Enable HEIC/HEIF support in Pillow (idempotent)."""
    global _registered
    if not _registered:
        register_heif_opener()
        _registered = True


def load(path: Path) -> Image.Image:
    """Open *path* as an RGBA image."""
    register()
    with Image.open(path) as opened:
        return opened.convert("RGBA")


def format_for(path: Path) -> str | None:
    """Pillow format name for *path*'s extension, or None if unsupported."""
    return _SAVE_FORMATS.get(path.suffix.lower())


def flatten(
    image: Image.Image, background: tuple[int, int, int] = _FLATTEN_BACKGROUND
) -> Image.Image:
    """Composite *image* onto an opaque *background*, dropping the alpha channel."""
    rgba = image.convert("RGBA")
    canvas = Image.new("RGB", rgba.size, background)
    canvas.paste(rgba, mask=rgba.getchannel("A"))
    return canvas


def save(image: Image.Image, path: Path) -> None:
    """Save *image* to *path*, choosing the format from its extension.

    Raises :class:`ValueError` for an unsupported extension.
    """
    register()
    fmt = format_for(path)
    if fmt is None:
        msg = f"unsupported output format: {path.suffix}"
        raise ValueError(msg)
    prepared = flatten(image) if fmt in _NO_ALPHA else image
    prepared.save(path, format=fmt)
