"""Application bootstrap."""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

from PySide6.QtWidgets import QApplication

from bluranything import __version__
from bluranything.ui.main_window import MainWindow

APP_NAME = "BLURAnything"
ORGANIZATION = "Safronus"


def parse_args(argv: list[str]) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        prog="bluranything",
        description="Blur sensitive parts of images and screenshots.",
    )
    parser.add_argument("image", nargs="?", type=Path, help="image file to open on startup")
    parser.add_argument("--version", action="version", version=f"%(prog)s {__version__}")
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    args = parse_args(sys.argv[1:] if argv is None else argv)

    # Reuse an existing QApplication (tests); Qt allows only one per process.
    existing = QApplication.instance()
    app = existing if isinstance(existing, QApplication) else QApplication(sys.argv)
    app.setApplicationName(APP_NAME)
    app.setApplicationVersion(__version__)
    app.setOrganizationName(ORGANIZATION)

    window = MainWindow()
    if args.image is not None:
        window.load_image(args.image)
    window.show()
    return app.exec()
