"""Version metadata sanity checks."""

import re

from bluranything import __version__


def test_version_is_semver() -> None:
    assert re.fullmatch(r"\d+\.\d+\.\d+", __version__)
