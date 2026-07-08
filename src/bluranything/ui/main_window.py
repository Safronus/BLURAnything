"""Main application window."""

from __future__ import annotations

from pathlib import Path

from PIL import Image
from PySide6.QtCore import QRect, QTimer
from PySide6.QtGui import QAction, QCloseEvent, QKeySequence
from PySide6.QtWidgets import (
    QFileDialog,
    QLabel,
    QMainWindow,
    QMessageBox,
    QSpinBox,
    QToolBar,
)

from bluranything import __version__
from bluranything.core.blur import DEFAULT_RADIUS, blur_region
from bluranything.ui.image_view import ImageView
from bluranything.ui.qt_image import pil_to_qpixmap, qimage_to_pil
from bluranything.ui.screenshot import grab_primary_screen

APP_TITLE = "BLURAnything"
FILE_FILTER = "Images (*.png *.jpg *.jpeg *.bmp *.webp)"
SCREENSHOT_DELAY_MS = 400
MAX_UNDO = 20


class MainWindow(QMainWindow):
    """Editor window: open/capture an image, drag to blur, save."""

    def __init__(self) -> None:
        super().__init__()
        self._image: Image.Image | None = None
        self._path: Path | None = None
        self._undo_stack: list[Image.Image] = []

        self._view = ImageView(self)
        self._view.region_selected.connect(self.apply_blur)
        self.setCentralWidget(self._view)

        self._radius = QSpinBox(self)
        self._radius.setRange(1, 100)
        self._radius.setValue(DEFAULT_RADIUS)
        self._radius.setSuffix(" px")
        self._radius.setToolTip("Blur radius")

        self._build_actions()
        self._build_menus()
        self._build_toolbar()

        self.statusBar().showMessage("Open an image or capture a screenshot, then drag to blur.")
        self.resize(1000, 700)
        self._refresh()

    # ------------------------------------------------------------------ setup

    def _build_actions(self) -> None:
        self._open_action = QAction("&Open…", self)
        self._open_action.setShortcut(QKeySequence.StandardKey.Open)
        self._open_action.triggered.connect(self._open_dialog)

        self._capture_action = QAction("&Capture Screenshot", self)
        self._capture_action.setShortcut("Ctrl+Shift+C")
        self._capture_action.triggered.connect(self.capture_screenshot)

        self._save_action = QAction("&Save", self)
        self._save_action.setShortcut(QKeySequence.StandardKey.Save)
        self._save_action.triggered.connect(self._save)

        self._save_as_action = QAction("Save &As…", self)
        self._save_as_action.setShortcut(QKeySequence.StandardKey.SaveAs)
        self._save_as_action.triggered.connect(self._save_as_dialog)

        self._undo_action = QAction("&Undo Blur", self)
        self._undo_action.setShortcut(QKeySequence.StandardKey.Undo)
        self._undo_action.triggered.connect(self.undo)

        self._quit_action = QAction("&Quit", self)
        self._quit_action.setShortcut(QKeySequence.StandardKey.Quit)
        self._quit_action.triggered.connect(self.close)

        self._about_action = QAction("&About BLURAnything", self)
        self._about_action.triggered.connect(self._about)

    def _build_menus(self) -> None:
        file_menu = self.menuBar().addMenu("&File")
        file_menu.addAction(self._open_action)
        file_menu.addAction(self._capture_action)
        file_menu.addSeparator()
        file_menu.addAction(self._save_action)
        file_menu.addAction(self._save_as_action)
        file_menu.addSeparator()
        file_menu.addAction(self._quit_action)

        edit_menu = self.menuBar().addMenu("&Edit")
        edit_menu.addAction(self._undo_action)

        help_menu = self.menuBar().addMenu("&Help")
        help_menu.addAction(self._about_action)

    def _build_toolbar(self) -> None:
        toolbar = QToolBar("Main", self)
        toolbar.setMovable(False)
        toolbar.addAction(self._open_action)
        toolbar.addAction(self._capture_action)
        toolbar.addAction(self._save_action)
        toolbar.addSeparator()
        toolbar.addWidget(QLabel("Radius: ", self))
        toolbar.addWidget(self._radius)
        toolbar.addSeparator()
        toolbar.addAction(self._undo_action)
        self.addToolBar(toolbar)

    # ------------------------------------------------------------- public API

    def load_image(self, path: Path) -> bool:
        """Open *path* as the working image. Returns True on success."""
        if not self._confirm_discard():
            return False
        try:
            with Image.open(path) as opened:
                image = opened.convert("RGBA")
        except (OSError, ValueError) as exc:
            QMessageBox.critical(self, APP_TITLE, f"Could not open {path}:\n{exc}")
            return False
        self._set_document(image, Path(path))
        self.statusBar().showMessage(f"Opened {path.name} ({image.width}×{image.height})")
        return True

    def apply_blur(self, rect: QRect) -> None:
        """Blur *rect* (image coordinates) on the working image."""
        if self._image is None:
            return
        box = (rect.left(), rect.top(), rect.left() + rect.width(), rect.top() + rect.height())
        blurred = blur_region(self._image, box, self._radius.value())

        self._undo_stack.append(self._image)
        del self._undo_stack[:-MAX_UNDO]
        self._image = blurred
        self.setWindowModified(True)
        self._show_image()
        self.statusBar().showMessage(
            f"Blurred {rect.width()}×{rect.height()} px at ({rect.left()}, {rect.top()})"
        )

    def undo(self) -> None:
        """Revert the most recent blur."""
        if not self._undo_stack:
            return
        self._image = self._undo_stack.pop()
        self._show_image()
        self.statusBar().showMessage("Undid last blur")

    def save_to(self, path: Path) -> bool:
        """Write the working image to *path*. Returns True on success."""
        if self._image is None:
            return False
        image = self._image
        if path.suffix.lower() in {".jpg", ".jpeg"}:
            image = image.convert("RGB")  # JPEG cannot store alpha
        try:
            image.save(path)
        except (OSError, ValueError) as exc:
            QMessageBox.critical(self, APP_TITLE, f"Could not save {path}:\n{exc}")
            return False
        self._path = path
        self.setWindowModified(False)
        self._refresh()
        self.statusBar().showMessage(f"Saved {path.name}")
        return True

    def capture_screenshot(self) -> None:
        """Hide the window briefly and capture the primary screen."""
        if not self._confirm_discard():
            return
        self.hide()
        QTimer.singleShot(SCREENSHOT_DELAY_MS, self._grab_and_show)

    @property
    def image(self) -> Image.Image | None:
        """The current working image (None before anything is opened)."""
        return self._image

    # ---------------------------------------------------------------- helpers

    def _grab_and_show(self) -> None:
        try:
            qimage = grab_primary_screen()
        finally:
            self.show()
        if qimage is None:
            QMessageBox.warning(
                self,
                APP_TITLE,
                "Screenshot failed. On macOS, allow Screen Recording for this app in "
                "System Settings → Privacy & Security.",
            )
            return
        self._set_document(qimage_to_pil(qimage), None)
        self.statusBar().showMessage("Captured screenshot — drag to blur, then save")

    def _set_document(self, image: Image.Image, path: Path | None) -> None:
        self._image = image
        self._path = path
        self._undo_stack.clear()
        self.setWindowModified(path is None)  # unsaved captures count as modified
        self._show_image()

    def _show_image(self) -> None:
        if self._image is not None:
            self._view.set_pixmap(pil_to_qpixmap(self._image))
        self._refresh()

    def _refresh(self) -> None:
        has_image = self._image is not None
        self._save_action.setEnabled(has_image)
        self._save_as_action.setEnabled(has_image)
        self._undo_action.setEnabled(bool(self._undo_stack))
        name = self._path.name if self._path else ("screenshot" if has_image else "no image")
        self.setWindowTitle(f"{name}[*] — {APP_TITLE}")

    def _confirm_discard(self) -> bool:
        if not self.isWindowModified():
            return True
        answer = QMessageBox.question(
            self,
            APP_TITLE,
            "You have unsaved changes. Discard them?",
            QMessageBox.StandardButton.Discard | QMessageBox.StandardButton.Cancel,
            QMessageBox.StandardButton.Cancel,
        )
        return answer == QMessageBox.StandardButton.Discard

    # ------------------------------------------------------------- Qt dialogs

    def _open_dialog(self) -> None:
        start_dir = str(self._path.parent) if self._path else str(Path.home())
        filename, _ = QFileDialog.getOpenFileName(self, "Open Image", start_dir, FILE_FILTER)
        if filename:
            self.load_image(Path(filename))

    def _save(self) -> None:
        if self._path is not None:
            self.save_to(self._path)
        else:
            self._save_as_dialog()

    def _save_as_dialog(self) -> None:
        if self._image is None:
            return
        start = str(self._path) if self._path else str(Path.home() / "blurred.png")
        filename, _ = QFileDialog.getSaveFileName(self, "Save Image", start, FILE_FILTER)
        if filename:
            self.save_to(Path(filename))

    def _about(self) -> None:
        QMessageBox.about(
            self,
            f"About {APP_TITLE}",
            f"<b>{APP_TITLE}</b> {__version__}<br>"
            "Blur sensitive parts of images and screenshots.<br>"
            '<a href="https://github.com/Safronus/BLURAnything">github.com/Safronus/BLURAnything</a>',
        )

    # ------------------------------------------------------------ Qt overrides

    def closeEvent(self, event: QCloseEvent) -> None:
        if self._confirm_discard():
            event.accept()
        else:
            event.ignore()
