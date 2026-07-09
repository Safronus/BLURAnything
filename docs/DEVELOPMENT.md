# Development Guide

## Prerequisites

- Python 3.11+
- `make`, `git`, and the [GitHub CLI](https://cli.github.com) (`gh`) for releases

## First-time setup

```bash
git clone https://github.com/Safronus/BLURAnything.git
cd BLURAnything
make setup
```

### The venv lives outside the repo (important)

This repository typically sits in an iCloud-synced folder (Desktop/Documents on macOS).
A virtualenv contains tens of thousands of small files that iCloud would try to sync —
slow, wasteful, and a common source of corrupted environments.

`make setup` therefore runs [`scripts/setup-venv.sh`](../scripts/setup-venv.sh), which:

1. creates the real venv at **`~/.venvs/bluranything`** (outside any synced folder),
2. symlinks it into the repo as **`.venv`** (the symlink is gitignored),
3. so every tool can still use the conventional `.venv/bin/...` paths.

Overrides: `VENV_HOME=/custom/dir make setup`, `PYTHON=python3.12 make setup`.
Never replace the symlink with a real in-repo venv.

## Everyday commands

| Command         | What it does                                     |
| --------------- | ------------------------------------------------ |
| `make run`      | launch the app from source                       |
| `make fmt`      | auto-format + autofix lint (ruff)                |
| `make check`    | **all quality gates** — run before every commit  |
| `make lint`     | ruff format check + lint                         |
| `make type`     | mypy (strict)                                    |
| `make test`     | pytest (GUI tests offscreen)                     |
| `make cov`      | tests with coverage report                       |
| `make deadcode` | vulture dead-code scan                           |
| `make audit`    | pip-audit vulnerability scan                     |
| `make build`    | build sdist + wheel into `dist/`                 |
| `make clean`    | remove caches and build artifacts                |

## CI

Every push to `main` and every PR runs (`.github/workflows/ci.yml`):

- **lint** — ruff format check, ruff lint, mypy strict, vulture
- **test** — pytest on Ubuntu (3.11, 3.13), macOS (3.13), Windows (3.13), offscreen Qt
- **audit** — pip-audit
- **CodeQL** — static security analysis (also weekly), `codeql.yml`

Dependabot updates Python deps and GitHub Actions weekly.

## Release process

1. Make sure `main` is green and the `[Unreleased]` changelog section is complete.
2. Move `[Unreleased]` entries into a new `## [X.Y.Z] - YYYY-MM-DD` section; update the
   link references at the bottom of `CHANGELOG.md`.
3. Bump `__version__` in `src/bluranything/__init__.py`.
4. Commit (`chore(release): vX.Y.Z`) and push.
5. Tag and push the tag:

   ```bash
   git tag -a vX.Y.Z -m "BLURAnything X.Y.Z"
   git push origin vX.Y.Z
   ```

6. The **Release** workflow re-runs all gates, verifies the tag matches
   `__version__`, builds sdist/wheel, extracts the changelog section and publishes the
   GitHub Release. Watch it: `gh run watch`.

Versioning follows [SemVer](https://semver.org): MAJOR = breaking, MINOR = features,
PATCH = fixes.

## Troubleshooting

- **`qt.qpa.plugin: could not load...` in tests/CI** — tests force
  `QT_QPA_PLATFORM=offscreen`; locally you can do the same for headless runs.
- **HEIC files won't open** — HEIC support comes from `pillow-heif` (a declared
  dependency); make sure the dev install (`make setup`) completed.
- **Broken `.venv` symlink** — re-run `./scripts/setup-venv.sh`.
