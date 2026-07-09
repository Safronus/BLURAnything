# Contributing to BLURAnything

Thanks for your interest! This document describes how to get set up and what a
change needs before it can be merged.

## Setup

```bash
git clone https://github.com/Safronus/BLURAnything.git
cd BLURAnything
make setup
```

`make setup` creates the virtualenv **outside** the repository (`~/.venvs/bluranything`,
override with `VENV_HOME`) and symlinks it as `.venv`. This keeps thousands of venv files
out of cloud-synced folders — do not create a real venv inside the repo.

## Quality gates

Every change must pass all gates before it lands on `main`:

```bash
make check    # = lint + type + test + deadcode
```

| Command         | What it does                                  |
| --------------- | --------------------------------------------- |
| `make fmt`      | auto-format (ruff) and fix lint issues        |
| `make lint`     | ruff format check + lint                      |
| `make type`     | mypy in strict mode                           |
| `make test`     | pytest (GUI tests run offscreen)              |
| `make cov`      | tests with coverage report                    |
| `make deadcode` | vulture dead-code scan                        |
| `make audit`    | pip-audit for vulnerable dependencies         |

Pre-commit hooks (installed by `make setup`) run ruff, mypy, vulture and basic
hygiene checks on every commit, so a red commit never reaches CI.

## Conventions

- **Commits:** [Conventional Commits](https://www.conventionalcommits.org) —
  `feat:`, `fix:`, `docs:`, `test:`, `ci:`, `refactor:`, `chore:`. English, imperative.
- **Changelog:** every user-visible change adds a bullet under `[Unreleased]` in
  `CHANGELOG.md` — in the same commit as the change.
- **Architecture:** `core/` stays free of Qt imports (pure Pillow, fully unit-testable);
  all Qt code lives in `ui/`. See [docs/ARCHITECTURE.md](docs/ARCHITECTURE.md).
- **Dead code:** delete it, don't comment it out. `make deadcode` must stay clean.
- **Dependencies:** prefer the standard library, Qt and Pillow. A new dependency needs
  a written justification in the PR.

## Tests

- Pure logic → plain pytest in `tests/test_blur.py`-style modules.
- GUI behaviour → `pytest-qt` with the offscreen platform (no display needed).
- Bug fixes come with a regression test.
