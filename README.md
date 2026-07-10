# BLURAnything

[![CI](https://github.com/Safronus/BLURAnything/actions/workflows/ci.yml/badge.svg)](https://github.com/Safronus/BLURAnything/actions/workflows/ci.yml)
[![CodeQL](https://github.com/Safronus/BLURAnything/actions/workflows/codeql.yml/badge.svg)](https://github.com/Safronus/BLURAnything/actions/workflows/codeql.yml)
[![Release](https://img.shields.io/github/v/release/Safronus/BLURAnything)](https://github.com/Safronus/BLURAnything/releases)
[![License: MIT](https://img.shields.io/github/license/Safronus/BLURAnything)](LICENSE)
[![Python 3.11+](https://img.shields.io/badge/python-3.11%2B-blue)](pyproject.toml)

Desktop app to quickly **blur sensitive parts of images and screenshots** before you share
them. Built with Python and PySide6 (Qt 6). Cross-platform: macOS, Windows, Linux.

## Features

- Open images (PNG, TIFF, JPG, HEIC, BMP, WebP), paste from the clipboard (⌘V),
  or drag & drop a file from Finder
- Redact regions with **rectangle, ellipse, polygon, freehand lasso and brush** tools
- **Automatic face blur** — detect and blur every face at once, or click a single
  face with the Face tool (offline, switchable YuNet/Haar detector)
- Effects: **Gaussian blur, pixelate/mosaic and solid fill**, with switchable
  soft (feathered) or hard edges
- Non-destructive editing with a live before/after — editor on the left, clean
  result preview on the right
- Undo / redo / clear, adjustable effect intensity and brush size
- Export to PNG/TIFF/JPG/HEIC/WebP/BMP or **PDF**, or copy the result to the clipboard
- **Autosave** with recovery after an unexpected close
- Dark, macOS-like theme
- **Czech** user interface (strings centralised, ready for more languages)

> **Privacy note:** Gaussian blur hides faces and visual context well, but heavily
> blurred *text* can sometimes be partially reconstructed. For sensitive text, prefer
> the **pixelate** or **solid fill** effect, which are not reversible.

## Installation

Requires Python 3.11+.

```bash
pip install "bluranything @ git+https://github.com/Safronus/BLURAnything@v0.2.0"
```

Or grab the wheel from the [latest release](https://github.com/Safronus/BLURAnything/releases)
and `pip install` it.

## Usage

```bash
bluranything                 # start the app
bluranything photo.png       # open an image right away
bluranything --version
```

1. **Open** an image (`Ctrl+O` / `⌘O`), **paste** one from the clipboard (`Ctrl+V` / `⌘V`),
   or **drag & drop** a file from Finder onto the editor.
2. Pick a **tool** (rectangle, ellipse, polygon, lasso, brush) and an **effect**
   (blur, pixelate, solid fill) in the toolbar, then draw over anything to hide.
3. Tune **intensity**, **brush size** and **soft/hard edges**; **undo / redo**
   (`⌘Z` / `⌘⇧Z`) as needed.
4. **Save** (`⌘S`) to PNG/TIFF/JPG/HEIC/WebP/BMP/PDF, or **copy** the result (`⌘C`).

> **macOS tip:** press ⌘⇧⌃4 to copy a screen area to the clipboard, then paste it
> straight into BLURAnything with ⌘V.

## Development

```bash
git clone https://github.com/Safronus/BLURAnything.git
cd BLURAnything
make setup    # creates the venv OUTSIDE the repo (~/.venvs/bluranything, iCloud-safe),
              # symlinks it as .venv, installs dev deps and pre-commit hooks
make check    # all quality gates: format, lint, types, tests, dead-code scan
make run      # launch the app from source
```

See [docs/DEVELOPMENT.md](docs/DEVELOPMENT.md) for the full guide (all make targets,
release process, project conventions) and
[docs/ARCHITECTURE.md](docs/ARCHITECTURE.md) for how the code is organized.

## Versioning & releases

The project follows [Semantic Versioning](https://semver.org) and keeps a human-readable
[CHANGELOG.md](CHANGELOG.md) ([Keep a Changelog](https://keepachangelog.com) format).
Pushing a `vX.Y.Z` tag runs the quality gates and publishes a GitHub Release with
changelog-driven notes and build artifacts automatically.

## Contributing & security

Contributions are welcome — see [CONTRIBUTING.md](CONTRIBUTING.md).
To report a vulnerability, please follow [SECURITY.md](SECURITY.md).

## License

[MIT](LICENSE) © 2026 Safronus
