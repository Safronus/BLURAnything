"""Tests for the release-notes extraction script (guards the release pipeline)."""

from __future__ import annotations

import subprocess
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).parents[1]
SCRIPT = REPO_ROOT / "scripts" / "release_notes.py"


def run_script(*args: str) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        [sys.executable, str(SCRIPT), *args],
        cwd=REPO_ROOT,
        capture_output=True,
        text=True,
        check=False,
    )


def test_extracts_current_release_section() -> None:
    result = run_script("0.1.0")
    assert result.returncode == 0
    assert "### Added" in result.stdout
    assert "## [" not in result.stdout  # only the section body, no headers


def test_unknown_version_fails() -> None:
    result = run_script("99.99.99")
    assert result.returncode == 1
    assert "not found" in result.stderr
