# CLAUDE.md — Project rules for AI-assisted development

## Project

BLURAnything — PySide6 desktop app for blurring parts of images and screenshots.
Public repo: https://github.com/Safronus/BLURAnything. `src` layout;
`core/` is pure Pillow (no Qt imports — unit-testable), `ui/` holds all Qt code.

## Environment

- The virtualenv lives **outside** the repo (`~/.venvs/bluranything`), symlinked as
  `.venv`. The repo sits in an iCloud-synced folder — **never create a real venv inside
  the repo**. Bootstrap with `make setup` (or `scripts/setup-venv.sh`).
- Run all tools through the venv: `make …` targets or `.venv/bin/python -m …`.

## Golden rules

1. **Ask, don't guess.** When requirements are ambiguous, ask the user — they prefer
   deciding themselves. Communicate with the user in Czech; repo content stays English.
2. **Quality gates before every commit:** `make check` (ruff format+lint, mypy strict,
   pytest, vulture) must be green. Fix, don't skip.
3. **Auto commit & push to `main`** after each completed, green change — no need to ask.
   Conventional Commits (`feat:`, `fix:`, `docs:`, `test:`, `ci:`, `refactor:`, `chore:`), English.
4. **Changelog discipline:** every user-visible change adds a bullet under
   `[Unreleased]` in `CHANGELOG.md` — in the same commit.
5. **Docs stay current:** update README / `docs/` whenever behaviour, commands or
   structure change.
6. **Dead code is deleted immediately**, never commented out. `make deadcode` stays clean;
   do a broader sweep (`vulture --min-confidence 60`) during refactors.
7. **Security:** no secrets in the repo; run `make audit` when dependencies change;
   new dependencies need explicit justification. CodeQL and Dependabot stay enabled.
8. **Tests accompany code:** new features get tests, bug fixes get regression tests.
   Pure logic goes to `core/` so it is testable without Qt.

## Release process (SemVer)

1. Move `[Unreleased]` entries into a new `## [X.Y.Z] - YYYY-MM-DD` section in
   `CHANGELOG.md` and update the link references at the bottom.
2. Bump `__version__` in `src/bluranything/__init__.py` — same commit,
   message `chore(release): vX.Y.Z`.
3. Push, then tag: `git tag -a vX.Y.Z -m "BLURAnything X.Y.Z"` and
   `git push origin vX.Y.Z`.
4. The Release workflow re-runs the gates, verifies tag == `__version__`, builds
   sdist/wheel and publishes the GitHub Release with notes extracted from the changelog.
   **Verify the workflow went green** (`gh run watch`).

## Commands

`make setup | check | fmt | lint | type | test | cov | deadcode | audit | run | build | clean`
