# Architecture

## Layers

```
┌──────────────────────────────────────────────────────────────┐
│ app.py — bootstrap: apply theme, register HEIF, parse CLI    │
├──────────────────────────────────────────────────────────────┤
│ ui/ — Qt layer (PySide6)                                     │
│   theme.py         dark macOS-like palette + stylesheet      │
│   main_window.py   toolbar, tools, effects, autosave, state  │
│   editor_canvas.py interactive canvas: tool gestures+overlay │
│   scaled_view.py   shared scaled image view + coord mapping  │
│   clipboard.py     paste / copy images                       │
│   qt_image.py      Pillow ↔ Qt conversions                   │
├──────────────────────────────────────────────────────────────┤
│ core/ — pure imaging & state (Pillow only, NO Qt)           │
│   document.py      base + mask + effect + edges; undo/redo   │
│   effects.py       Effect protocol; blur/pixelate/solid      │
│   mask.py          stamp rect/ellipse/polygon/stroke; feather│
│   compositor.py    blend base + effect layer through a mask  │
│   faces.py         offline face detection (YuNet / Haar)     │
│   imageio.py       load/save incl. HEIC and PDF              │
│   session.py       autosave / recovery serialization         │
└──────────────────────────────────────────────────────────────┘
```

**Rule: `core/` must never import Qt.** All imaging and editing state lives there,
so the whole model is unit-testable without a GUI and could back a future CLI.

## The document model

A `Document` is the single source of truth and edits are **non-destructive**:

- It holds the original `base` image, an `L`-mode selection **mask**, the current
  `Effect` and the edge mode (soft/hard + feather radius).
- Tools stamp opaque shapes into the mask (`mask.py`); the base is never modified.
- `render()` composites on demand: it caches the effect applied to the whole image
  (the expensive step) and blends it onto the base through the mask — feathered when
  edges are soft. An empty mask renders as the untouched original.
- Undo/redo snapshot the mask (one entry per stroke; a brush drag collapses into one).

Effects are frozen dataclasses implementing a tiny `Effect` protocol
(`apply(image) -> image`), so they compare by value (used for the render cache) and
new effects are trivial to add. `effect_from(kind, value)` builds one from a stable
key, shared by the toolbar and session restore.

## Data flow

1. `MainWindow` loads an image from disk (`imageio.load`, HEIC via pillow-heif) or the
   clipboard (`clipboard.image_from_clipboard`) and wraps it in a `Document`.
2. `EditorCanvas` maps mouse gestures to image pixels and calls the matching
   `Document.stamp_*`. Gestures are plain methods (`begin/extend/finish_gesture`,
   `finish_polygon`, `cancel`), so tools are testable without synthetic Qt events.
3. On any change the window renders **once** and shows the result in both panes; the
   editor additionally tints the selected regions and draws the in-progress shape.
4. Edits debounce an **autosave** (`session.save_session`) to a temp directory; it is
   cleared on save/clean-close and offered back for recovery on the next launch.
5. Export writes the rendered result with `imageio.save` (format from the extension,
   including PDF) or copies it to the clipboard.

## Testing strategy

- `core/` — plain pytest with deterministic checkerboard fixtures (`tests/helpers.py`):
  effects, mask stamps, compositor, document (render/undo/edges/effects) and sessions.
- `ui/` — pytest-qt on the `offscreen` platform (set in `tests/conftest.py` and CI):
  the canvas gesture API and the window's public API (load, paste, tools, effects,
  save, copy, autosave/recovery).
