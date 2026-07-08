# Architecture

## Layers

```
┌────────────────────────────────────────────────┐
│ app.py — bootstrap (QApplication, CLI args)    │
├────────────────────────────────────────────────┤
│ ui/ — Qt layer (PySide6)                       │
│   main_window.py  actions, menus, state        │
│   image_view.py   canvas + rubber-band select  │
│   screenshot.py   QScreen capture              │
│   qt_image.py     Pillow ↔ Qt conversions      │
├────────────────────────────────────────────────┤
│ core/ — pure imaging (Pillow only, NO Qt)      │
│   blur.py         blur_region, clamp_box       │
└────────────────────────────────────────────────┘
```

**Rule: `core/` must never import Qt.** That keeps the image-processing logic
unit-testable without a GUI environment and portable to a future CLI mode.

## Data flow

1. `MainWindow.load_image()` opens the file with Pillow and normalizes it to RGBA;
   `capture_screenshot()` grabs a `QImage` and converts it via `qt_image.qimage_to_pil`.
2. The working image (a Pillow `Image`) is the single source of truth, held by
   `MainWindow._image`. The view only ever renders a `QPixmap` copy of it.
3. `ImageView` maps a completed rubber-band drag to image pixel coordinates
   (pixmap sits at the scene origin, so scene coords == pixel coords) and emits
   `region_selected(QRect)`.
4. `MainWindow.apply_blur()` calls `core.blur.blur_region()` — which clamps the box,
   blurs a copy and returns it — pushes the previous image onto the undo stack
   (capped at 20) and re-renders.
5. `save_to()` writes with Pillow, converting RGBA→RGB for JPEG targets.

## Testing strategy

- `core/` — plain pytest, deterministic checkerboard fixtures (`tests/helpers.py`).
- `ui/` — pytest-qt against the public `MainWindow` API (`load_image`, `apply_blur`,
  `undo`, `save_to`), running on the `offscreen` Qt platform so no display is needed
  (set in `tests/conftest.py` and in CI).
- `scripts/` — the release-notes extractor is covered by subprocess tests, because a
  broken extractor would break the release pipeline.
