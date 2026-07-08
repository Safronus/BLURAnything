#!/usr/bin/env python3
"""Print the CHANGELOG.md section for a version (used by the release workflow)."""

from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path


def extract_section(changelog: str, version: str) -> str | None:
    """Return the body of the ``## [version]`` section, or None when missing."""
    pattern = rf"^## \[{re.escape(version)}\][^\n]*\n(.*?)(?=^## \[|^\[|\Z)"
    match = re.search(pattern, changelog, re.DOTALL | re.MULTILINE)
    if match is None:
        return None
    return match.group(1).strip()


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("version", help="version to extract, e.g. 0.1.0")
    parser.add_argument(
        "--changelog",
        type=Path,
        default=Path("CHANGELOG.md"),
        help="path to the changelog (default: CHANGELOG.md)",
    )
    args = parser.parse_args()

    section = extract_section(args.changelog.read_text(encoding="utf-8"), args.version)
    if section is None:
        print(f"error: version {args.version} not found in {args.changelog}", file=sys.stderr)
        return 1
    print(section)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
