"""Shared test configuration."""

import os

# Run Qt headless everywhere (local runs, CI) before any QApplication is created.
os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")
