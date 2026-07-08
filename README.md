# BLURAnything

[![CI](https://github.com/Safronus/BLURAnything/actions/workflows/ci.yml/badge.svg)](https://github.com/Safronus/BLURAnything/actions/workflows/ci.yml)
[![CodeQL](https://github.com/Safronus/BLURAnything/actions/workflows/codeql.yml/badge.svg)](https://github.com/Safronus/BLURAnything/actions/workflows/codeql.yml)
[![Release](https://img.shields.io/github/v/release/Safronus/BLURAnything)](https://github.com/Safronus/BLURAnything/releases)
[![License: MIT](https://img.shields.io/github/license/Safronus/BLURAnything)](LICENSE)
[![Python 3.11+](https://img.shields.io/badge/python-3.11%2B-blue)](pyproject.toml)

Desktop app to quickly **blur sensitive parts of images and screenshots** before you share
them. Built with Python and PySide6 (Qt 6). Cross-platform: macOS, Windows, Linux.

## Features

- Open an image (PNG, JPEG, BMP, WebP) and blur any region by simply dragging a rectangle
- Capture a screenshot of your primary screen straight into the editor
- Adjustable Gaussian blur radius (1–100 px)
- Undo for blur operations (up to 20 steps), unsaved-changes protection
- Save or Save As, with automatic alpha handling for JPEG

> **Privacy note:** Gaussian blur is great for hiding faces and visual context, but heavily
> blurred *text* can sometimes be partially reconstructed. Irreversible modes (pixelate,
> solid fill) are on the roadmap — see the issue tracker.

## Installation

Requires Python 3.11+.

```bash
pip install "bluranything @ git+https://github.com/Safronus/BLURAnything@v0.1.0"
```

Or grab the wheel from the [latest release](https://github.com/Safronus/BLURAnything/releases)
and `pip install` it.

## Usage

```bash
bluranything                 # start the app
bluranything photo.png       # open an image right away
bluranything --version
```

1. **Open** an image (`Ctrl+O` / `⌘O`) or **capture a screenshot** (`Ctrl+Shift+C`).
2. **Drag** a rectangle over anything you want to hide — it blurs immediately.
3. Adjust the **radius** in the toolbar, **undo** (`Ctrl+Z` / `⌘Z`) if needed.
4. **Save** (`Ctrl+S` / `⌘S`).

> **macOS:** screenshot capture requires the Screen Recording permission
> (System Settings → Privacy & Security → Screen Recording).

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
