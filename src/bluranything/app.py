"""Application bootstrap."""

from __future__ import annotations

import argparse
import sys
from importlib import resources
from pathlib import Path

from PySide6.QtCore import QLibraryInfo, QTranslator
from PySide6.QtGui import QIcon, QPixmap
from PySide6.QtWidgets import QApplication

from bluranything import __version__
from bluranything.core import imageio
from bluranything.ui.main_window import MainWindow
from bluranything.ui.theme import apply_theme

APP_NAME = "BLURAnything"
ORGANIZATION = "Safronus"


def parse_args(argv: list[str]) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        prog="bluranything",
        description="Rozmažte citlivé části obrázků a screenshotů.",
    )
    parser.add_argument("image", nargs="?", type=Path, help="obrázek k otevření po spuštění")
    parser.add_argument("--version", action="version", version=f"%(prog)s {__version__}")
    return parser.parse_args(argv)


def load_icon() -> QIcon:
    """The application icon, or an empty icon if the resource is unavailable."""
    icon = QIcon()
    try:
        data = (resources.files("bluranything.resources") / "icon.png").read_bytes()
    except (FileNotFoundError, ModuleNotFoundError):
        return icon
    pixmap = QPixmap()
    if pixmap.loadFromData(data):
        icon.addPixmap(pixmap)
    return icon


def install_czech(app: QApplication) -> None:
    """Localise Qt's standard dialogs/buttons to Czech when translations exist."""
    translations = QLibraryInfo.path(QLibraryInfo.LibraryPath.TranslationsPath)
    for name in ("qtbase_cs", "qt_cs"):
        translator = QTranslator(app)
        if translator.load(name, translations):
            app.installTranslator(translator)


def main(argv: list[str] | None = None) -> int:
    args = parse_args(sys.argv[1:] if argv is None else argv)

    existing = QApplication.instance()
    app = existing if isinstance(existing, QApplication) else QApplication(sys.argv)
    app.setApplicationName(APP_NAME)
    app.setApplicationVersion(__version__)
    app.setOrganizationName(ORGANIZATION)
    app.setWindowIcon(load_icon())
    apply_theme(app)
    install_czech(app)
    imageio.register()

    window = MainWindow()
    if args.image is not None:
        window.load_path(args.image)
    window.show()
    return app.exec()
