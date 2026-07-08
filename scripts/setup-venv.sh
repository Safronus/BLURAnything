#!/usr/bin/env bash
# Creates the project virtualenv OUTSIDE the repository and symlinks it as .venv.
#
# Rationale: this repository may live in an iCloud-synced folder (Desktop/Documents).
# A virtualenv contains tens of thousands of small files that iCloud would try to
# sync, which is slow and can corrupt the environment. Keeping the real venv under
# ~/.venvs and only symlinking it into the repo avoids all of that.
#
# Usage: ./scripts/setup-venv.sh
#   VENV_HOME=/custom/path ./scripts/setup-venv.sh   # override venv parent dir
#   PYTHON=python3.12 ./scripts/setup-venv.sh        # override interpreter
set -euo pipefail

PROJECT_NAME="bluranything"
VENV_HOME="${VENV_HOME:-$HOME/.venvs}"
VENV_PATH="$VENV_HOME/$PROJECT_NAME"
PYTHON="${PYTHON:-python3}"

mkdir -p "$VENV_HOME"

if [ ! -x "$VENV_PATH/bin/python" ]; then
    echo "Creating virtualenv at $VENV_PATH"
    "$PYTHON" -m venv "$VENV_PATH"
else
    echo "Virtualenv already exists at $VENV_PATH"
fi

cd "$(dirname "$0")/.."
ln -snf "$VENV_PATH" .venv
echo "Symlinked .venv -> $VENV_PATH"
echo "Next: make setup (or: .venv/bin/pip install -e '.[dev]')"
