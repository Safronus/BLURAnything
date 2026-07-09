# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

### Added

- Non-destructive editor: open (PNG/TIFF/JPG/HEIC/BMP/WebP) or paste from the
  clipboard (⌘V) an image and blur a region by dragging a rectangle.
- Split view — interactive editor on the left, live result preview on the right.
- Adjustable Gaussian blur intensity with switchable soft (feathered) / hard edges.
- Undo, redo and clear-all for edits.
- Save the result to PNG, TIFF, JPG, HEIC, WebP, BMP or PDF.
- Dark, macOS-like theme.

### Changed

- Reworked the app around a Qt-free imaging core (effects, mask, compositor,
  document) so the whole editing model is unit-testable without a GUI.

### Removed

- Direct screen-capture action — superseded by clipboard paste (⌘⇧⌃4 on macOS
  copies a screenshot straight to the clipboard). May return later if needed.

## [0.1.0] - 2026-07-08

### Added

- Image editor: open PNG/JPEG/BMP/WebP files and blur selected regions by dragging.
- Adjustable Gaussian blur radius (1–100 px).
- Screenshot capture of the primary screen straight into the editor.
- Undo for blur operations (up to 20 steps) and unsaved-changes protection.
- Save / Save As with automatic alpha-channel handling for JPEG.
- Quality tooling: ruff, mypy (strict), pytest + pytest-qt, vulture, pip-audit, pre-commit.
- CI on Linux/macOS/Windows, CodeQL scanning, Dependabot updates.
- Automated GitHub Releases from `vX.Y.Z` tags with changelog-driven notes.

[Unreleased]: https://github.com/Safronus/BLURAnything/compare/v0.1.0...HEAD
[0.1.0]: https://github.com/Safronus/BLURAnything/releases/tag/v0.1.0
