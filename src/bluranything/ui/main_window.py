"""Main application window: editor on the left, live preview on the right."""

from __future__ import annotations

from pathlib import Path

from PySide6.QtCore import Qt
from PySide6.QtGui import QAction, QCloseEvent, QKeySequence
from PySide6.QtWidgets import (
    QCheckBox,
    QFileDialog,
    QLabel,
    QMainWindow,
    QMessageBox,
    QSlider,
    QSplitter,
    QToolBar,
)

from bluranything import __version__
from bluranything.core import imageio
from bluranything.core.document import Document, EdgeMode
from bluranything.core.effects import DEFAULT_BLUR_RADIUS, GaussianBlurEffect
from bluranything.ui.clipboard import image_from_clipboard
from bluranything.ui.editor_canvas import EditorCanvas
from bluranything.ui.scaled_view import ScaledImageView

APP_TITLE = "BLURAnything"
DEFAULT_FEATHER = 6

_OPEN_FILTER = "Images (" + " ".join(f"*{ext}" for ext in imageio.INPUT_EXTENSIONS) + ")"
_SAVE_FILTER = ";;".join(
    (
        "PNG (*.png)",
        "JPEG (*.jpg)",
        "TIFF (*.tiff)",
        "HEIC (*.heic)",
        "WebP (*.webp)",
        "BMP (*.bmp)",
        "PDF (*.pdf)",
    )
)


class MainWindow(QMainWindow):
    """Open or paste an image, blur regions non-destructively, then save."""

    def __init__(self) -> None:
        super().__init__()
        self._document: Document | None = None
        self._path: Path | None = None
        self._dirty = False

        self._editor = EditorCanvas(self)
        self._editor.changed.connect(self._on_edit)
        self._preview = ScaledImageView(placeholder="Preview", parent=self)

        splitter = QSplitter(Qt.Orientation.Horizontal, self)
        splitter.addWidget(self._editor)
        splitter.addWidget(self._preview)
        splitter.setSizes([600, 600])
        self.setCentralWidget(splitter)

        self._intensity = self._make_slider(1, 100, DEFAULT_BLUR_RADIUS)
        self._feather = self._make_slider(0, 40, DEFAULT_FEATHER)
        self._soft_edges = QCheckBox("Soft edges", self)
        self._soft_edges.setChecked(True)

        self._build_actions()
        self._build_menus()
        self._build_toolbar()
        self._connect_controls()

        self.setStatusBar(self.statusBar())
        self.statusBar().showMessage("Open an image or paste (⌘V), then drag to blur.")
        self.resize(1180, 760)
        self._refresh()

    # ------------------------------------------------------------------ setup

    @staticmethod
    def _make_slider(minimum: int, maximum: int, value: int) -> QSlider:
        slider = QSlider(Qt.Orientation.Horizontal)
        slider.setRange(minimum, maximum)
        slider.setValue(value)
        slider.setFixedWidth(120)
        return slider

    def _build_actions(self) -> None:
        self._open_action = QAction("&Open…", self)
        self._open_action.setShortcut(QKeySequence.StandardKey.Open)
        self._open_action.triggered.connect(self._open_dialog)

        self._paste_action = QAction("&Paste", self)
        self._paste_action.setShortcut(QKeySequence.StandardKey.Paste)
        self._paste_action.triggered.connect(self.paste_from_clipboard)

        self._save_action = QAction("&Save…", self)
        self._save_action.setShortcut(QKeySequence.StandardKey.Save)
        self._save_action.triggered.connect(self._save)

        self._undo_action = QAction("&Undo", self)
        self._undo_action.setShortcut(QKeySequence.StandardKey.Undo)
        self._undo_action.triggered.connect(self.undo)

        self._redo_action = QAction("&Redo", self)
        self._redo_action.setShortcut(QKeySequence.StandardKey.Redo)
        self._redo_action.triggered.connect(self.redo)

        self._clear_action = QAction("Clear &All", self)
        self._clear_action.triggered.connect(self.clear)

        self._quit_action = QAction("&Quit", self)
        self._quit_action.setShortcut(QKeySequence.StandardKey.Quit)
        self._quit_action.triggered.connect(self.close)

        self._about_action = QAction("&About BLURAnything", self)
        self._about_action.triggered.connect(self._about)

    def _build_menus(self) -> None:
        file_menu = self.menuBar().addMenu("&File")
        file_menu.addAction(self._open_action)
        file_menu.addAction(self._paste_action)
        file_menu.addSeparator()
        file_menu.addAction(self._save_action)
        file_menu.addSeparator()
        file_menu.addAction(self._quit_action)

        edit_menu = self.menuBar().addMenu("&Edit")
        edit_menu.addAction(self._undo_action)
        edit_menu.addAction(self._redo_action)
        edit_menu.addSeparator()
        edit_menu.addAction(self._clear_action)

        help_menu = self.menuBar().addMenu("&Help")
        help_menu.addAction(self._about_action)

    def _build_toolbar(self) -> None:
        toolbar = QToolBar("Main", self)
        toolbar.setMovable(False)
        toolbar.addAction(self._open_action)
        toolbar.addAction(self._paste_action)
        toolbar.addAction(self._save_action)
        toolbar.addSeparator()
        toolbar.addWidget(QLabel("Blur", self))
        toolbar.addWidget(self._intensity)
        toolbar.addWidget(self._soft_edges)
        toolbar.addWidget(QLabel("Feather", self))
        toolbar.addWidget(self._feather)
        toolbar.addSeparator()
        toolbar.addAction(self._undo_action)
        toolbar.addAction(self._redo_action)
        self.addToolBar(toolbar)

    def _connect_controls(self) -> None:
        self._intensity.valueChanged.connect(self._on_effect_changed)
        self._feather.valueChanged.connect(self._on_effect_changed)
        self._soft_edges.toggled.connect(self._on_effect_changed)

    # ------------------------------------------------------------- public API

    def load_path(self, path: Path) -> bool:
        """Open *path* as the working image. Returns True on success."""
        if not self._confirm_discard():
            return False
        try:
            image = imageio.load(path)
        except (OSError, ValueError) as exc:
            QMessageBox.critical(self, APP_TITLE, f"Could not open {path}:\n{exc}")
            return False
        self._set_document(Document(image), Path(path))
        self.statusBar().showMessage(f"Opened {path.name} ({image.width}×{image.height})")
        return True

    def paste_from_clipboard(self) -> bool:
        """Load an image from the clipboard. Returns True on success."""
        if not self._confirm_discard():
            return False
        image = image_from_clipboard()
        if image is None:
            QMessageBox.information(self, APP_TITLE, "The clipboard does not contain an image.")
            return False
        self._set_document(Document(image), None)
        self.statusBar().showMessage(f"Pasted image ({image.width}×{image.height})")
        return True

    def save_to(self, path: Path) -> bool:
        """Write the rendered result to *path*. Returns True on success."""
        if self._document is None:
            return False
        try:
            imageio.save(self._document.render(), path)
        except (OSError, ValueError) as exc:
            QMessageBox.critical(self, APP_TITLE, f"Could not save {path}:\n{exc}")
            return False
        self._path = path
        self._dirty = False
        self._refresh()
        self.statusBar().showMessage(f"Saved {path.name}")
        return True

    def undo(self) -> None:
        if self._document is not None and self._document.can_undo:
            self._document.undo()
            self._after_change()

    def redo(self) -> None:
        if self._document is not None and self._document.can_redo:
            self._document.redo()
            self._after_change()

    def clear(self) -> None:
        if self._document is not None and not self._document.is_empty:
            self._document.clear_mask()
            self._after_change()

    @property
    def document(self) -> Document | None:
        return self._document

    @property
    def editor(self) -> EditorCanvas:
        return self._editor

    # ---------------------------------------------------------------- helpers

    def _current_effect(self) -> GaussianBlurEffect:
        return GaussianBlurEffect(self._intensity.value())

    def _apply_settings(self) -> None:
        if self._document is None:
            return
        self._document.set_effect(self._current_effect())
        mode = EdgeMode.SOFT if self._soft_edges.isChecked() else EdgeMode.HARD
        self._document.set_edge_mode(mode)
        self._document.set_feather(self._feather.value())

    def _set_document(self, document: Document, path: Path | None) -> None:
        self._document = document
        self._path = path
        self._dirty = False
        self._apply_settings()
        self._editor.set_document(document)
        self._refresh()

    def _on_edit(self) -> None:
        self._dirty = True
        self._after_change()

    def _on_effect_changed(self) -> None:
        self._feather.setEnabled(self._soft_edges.isChecked())
        if self._document is None:
            return
        self._apply_settings()
        if not self._document.is_empty:
            self._dirty = True
        self._after_change()

    def _after_change(self) -> None:
        if self._document is not None:
            self._editor.show_result(self._document.render())
            self._preview.set_image(self._document.render())
        self._refresh()

    def _refresh(self) -> None:
        doc = self._document
        has_doc = doc is not None
        self._save_action.setEnabled(has_doc)
        self._undo_action.setEnabled(doc is not None and doc.can_undo)
        self._redo_action.setEnabled(doc is not None and doc.can_redo)
        self._clear_action.setEnabled(doc is not None and not doc.is_empty)
        self._feather.setEnabled(self._soft_edges.isChecked())
        name = self._path.name if self._path else ("pasted image" if has_doc else "no image")
        self.setWindowModified(self._dirty)
        self.setWindowTitle(f"{name}[*] — {APP_TITLE}")

    def _confirm_discard(self) -> bool:
        if not self._dirty:
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
        start = str(self._path.parent) if self._path else str(Path.home())
        filename, _ = QFileDialog.getOpenFileName(self, "Open Image", start, _OPEN_FILTER)
        if filename:
            self.load_path(Path(filename))

    def _save(self) -> None:
        if self._document is None:
            return
        start = str(self._path) if self._path else str(Path.home() / "blurred.png")
        filename, _ = QFileDialog.getSaveFileName(self, "Save Image", start, _SAVE_FILTER)
        if not filename:
            return
        path = Path(filename)
        if path.suffix == "":
            path = path.with_suffix(".png")
        self.save_to(path)

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
