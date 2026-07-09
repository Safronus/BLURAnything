"""Main application window: editor on the left, live preview on the right."""

from __future__ import annotations

import tempfile
from pathlib import Path

from PySide6.QtCore import Qt, QTimer
from PySide6.QtGui import QAction, QCloseEvent, QKeySequence
from PySide6.QtWidgets import (
    QCheckBox,
    QComboBox,
    QFileDialog,
    QLabel,
    QMainWindow,
    QMessageBox,
    QSlider,
    QSplitter,
    QToolBar,
)

from bluranything import __version__
from bluranything.core import imageio, session
from bluranything.core.document import Document, EdgeMode
from bluranything.core.effects import (
    DEFAULT_BLUR_RADIUS,
    DEFAULT_PIXEL_SIZE,
    Effect,
    effect_from,
)
from bluranything.ui.clipboard import image_from_clipboard, image_to_clipboard
from bluranything.ui.editor_canvas import DEFAULT_BRUSH_RADIUS, EditorCanvas, Tool
from bluranything.ui.scaled_view import ScaledImageView

APP_TITLE = "BLURAnything"
DEFAULT_FEATHER = 6
AUTOSAVE_DEBOUNCE_MS = 2500
_DEFAULT_AUTOSAVE_DIR = Path(tempfile.gettempdir()) / "bluranything" / "autosave"

#: Selectable effects: (combo label, key, slider caption, slider min, max, default).
#: A zero range means the intensity slider does not apply (e.g. solid fill).
_EFFECT_KINDS: tuple[tuple[str, str, str, int, int, int], ...] = (
    ("Blur", "blur", "Blur", 1, 100, DEFAULT_BLUR_RADIUS),
    ("Pixelate", "pixelate", "Pixel size", 2, 64, DEFAULT_PIXEL_SIZE),
    ("Solid fill", "solid", "Solid", 0, 0, 0),
)

#: Selectable tools shown in the toolbar, in order.
_TOOLS: tuple[tuple[str, Tool], ...] = (
    ("Rectangle", Tool.RECTANGLE),
    ("Ellipse", Tool.ELLIPSE),
    ("Polygon", Tool.POLYGON),
    ("Lasso", Tool.LASSO),
    ("Brush", Tool.BRUSH),
)

_TOOL_HINTS = {
    Tool.RECTANGLE: "Rectangle — drag to blur a box.",
    Tool.ELLIPSE: "Ellipse — drag to blur an oval.",
    Tool.POLYGON: "Polygon — click points, double-click to close.",
    Tool.LASSO: "Lasso — drag to draw a freehand area.",
    Tool.BRUSH: "Brush — drag to paint blur.",
}

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

    def __init__(self, autosave_dir: Path | None = None) -> None:
        super().__init__()
        self._document: Document | None = None
        self._path: Path | None = None
        self._dirty = False
        self._autosave_dir = autosave_dir or _DEFAULT_AUTOSAVE_DIR
        self._autosave_timer = QTimer(self)
        self._autosave_timer.setInterval(AUTOSAVE_DEBOUNCE_MS)
        self._autosave_timer.setSingleShot(True)
        self._autosave_timer.timeout.connect(self._write_autosave)

        self._editor = EditorCanvas(self)
        self._editor.changed.connect(self._on_edit)
        self._preview = ScaledImageView(placeholder="Preview", parent=self)

        splitter = QSplitter(Qt.Orientation.Horizontal, self)
        splitter.addWidget(self._editor)
        splitter.addWidget(self._preview)
        splitter.setSizes([600, 600])
        self.setCentralWidget(splitter)

        self._tool_combo = QComboBox(self)
        for tool_label, tool in _TOOLS:
            self._tool_combo.addItem(tool_label, tool.value)
        self._brush_label = QLabel("Brush", self)
        self._brush = self._make_slider(4, 80, DEFAULT_BRUSH_RADIUS)
        self._brush.setEnabled(False)
        self._brush_label.setEnabled(False)

        self._effect_combo = QComboBox(self)
        for label, key, *_ in _EFFECT_KINDS:
            self._effect_combo.addItem(label, key)
        self._intensity_label = QLabel("Blur", self)
        self._intensity = self._make_slider(1, 100, DEFAULT_BLUR_RADIUS)
        self._feather = self._make_slider(0, 40, DEFAULT_FEATHER)
        self._soft_edges = QCheckBox("Soft edges", self)
        self._soft_edges.setChecked(True)

        self._build_actions()
        self._build_menus()
        self._build_toolbar()
        self._connect_controls()
        self._configure_intensity()

        self.setStatusBar(self.statusBar())
        self.statusBar().showMessage("Open an image or paste (⌘V), then drag to blur.")
        self.resize(1180, 760)
        self._refresh()
        self._maybe_offer_recovery()

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

        self._copy_action = QAction("&Copy Result", self)
        self._copy_action.setShortcut(QKeySequence.StandardKey.Copy)
        self._copy_action.triggered.connect(self.copy_result)

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
        edit_menu.addAction(self._copy_action)
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
        toolbar.addWidget(self._tool_combo)
        toolbar.addWidget(self._brush_label)
        toolbar.addWidget(self._brush)
        toolbar.addSeparator()
        toolbar.addWidget(self._effect_combo)
        toolbar.addWidget(self._intensity_label)
        toolbar.addWidget(self._intensity)
        toolbar.addWidget(self._soft_edges)
        toolbar.addWidget(QLabel("Feather", self))
        toolbar.addWidget(self._feather)
        toolbar.addSeparator()
        toolbar.addAction(self._undo_action)
        toolbar.addAction(self._redo_action)
        self.addToolBar(toolbar)

    def _connect_controls(self) -> None:
        self._tool_combo.currentIndexChanged.connect(self._on_tool_changed)
        self._brush.valueChanged.connect(self._editor.set_brush_radius)
        self._effect_combo.currentIndexChanged.connect(self._on_effect_kind_changed)
        self._intensity.valueChanged.connect(self._on_effect_changed)
        self._feather.valueChanged.connect(self._on_effect_changed)
        self._soft_edges.toggled.connect(self._on_effect_changed)

    def _on_tool_changed(self) -> None:
        tool = Tool(self._tool_combo.currentData())
        self._editor.set_tool(tool)
        is_brush = tool is Tool.BRUSH
        self._brush.setEnabled(is_brush)
        self._brush_label.setEnabled(is_brush)
        self.statusBar().showMessage(_TOOL_HINTS[tool])

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
        self._clear_autosave()
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

    def copy_result(self) -> None:
        """Copy the rendered result to the system clipboard."""
        if self._document is not None:
            image_to_clipboard(self._document.render())
            self.statusBar().showMessage("Copied result to the clipboard")

    @property
    def document(self) -> Document | None:
        return self._document

    @property
    def editor(self) -> EditorCanvas:
        return self._editor

    # ---------------------------------------------------------------- helpers

    def _current_effect(self) -> Effect:
        return effect_from(self._effect_combo.currentData(), self._intensity.value())

    def _configure_intensity(self) -> None:
        """Match the intensity slider's range, caption and state to the effect."""
        kind = self._effect_combo.currentData()
        _, _, caption, minimum, maximum, default = next(
            spec for spec in _EFFECT_KINDS if spec[1] == kind
        )
        self._intensity_label.setText(caption)
        applies = maximum > 0
        self._intensity.setEnabled(applies)
        if applies:
            value = min(max(self._intensity.value(), minimum), maximum) or default
            self._intensity.blockSignals(True)
            self._intensity.setRange(minimum, maximum)
            self._intensity.setValue(value)
            self._intensity.blockSignals(False)

    def _on_effect_kind_changed(self) -> None:
        self._configure_intensity()
        self._on_effect_changed()

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
            image = self._document.render()
            self._editor.show_result(image)
            self._preview.set_image(image)
        if self._dirty:
            self._autosave_timer.start()  # debounced write
        self._refresh()

    def _refresh(self) -> None:
        doc = self._document
        has_doc = doc is not None
        self._save_action.setEnabled(has_doc)
        self._copy_action.setEnabled(has_doc)
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

    # -------------------------------------------------------------- autosave

    def _write_autosave(self) -> None:
        if self._document is None or not self._dirty:
            return
        session.save_session(
            self._autosave_dir,
            self._document.base,
            self._document.mask_copy(),
            effect_kind=self._effect_combo.currentData(),
            effect_value=self._intensity.value(),
            edge_mode="soft" if self._soft_edges.isChecked() else "hard",
            feather=self._feather.value(),
            source=str(self._path) if self._path else None,
        )

    def _clear_autosave(self) -> None:
        self._autosave_timer.stop()
        session.clear_session(self._autosave_dir)

    def _maybe_offer_recovery(self) -> None:
        restored = session.load_session(self._autosave_dir)
        if restored is None:
            return
        answer = QMessageBox.question(
            self,
            APP_TITLE,
            "Recover unsaved work from the previous session?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
            QMessageBox.StandardButton.Yes,
        )
        if answer == QMessageBox.StandardButton.Yes:
            self._restore_session(restored)
        else:
            session.clear_session(self._autosave_dir)

    def _restore_session(self, restored: session.RestoredSession) -> None:
        document = Document(restored.base)
        document.set_mask(restored.mask)
        self._document = document
        self._path = Path(restored.source) if restored.source else None
        controls = (self._effect_combo, self._intensity, self._feather, self._soft_edges)
        for control in controls:
            control.blockSignals(True)
        self._effect_combo.setCurrentIndex(self._effect_index(restored.effect_kind))
        self._configure_intensity()
        if restored.effect_value:
            self._intensity.setValue(restored.effect_value)
        self._soft_edges.setChecked(restored.edge_mode == "soft")
        self._feather.setValue(restored.feather)
        for control in controls:
            control.blockSignals(False)
        self._apply_settings()
        self._editor.set_document(document)
        self._dirty = True
        self._after_change()
        self.statusBar().showMessage("Recovered unsaved work")

    def _effect_index(self, kind: str) -> int:
        for index in range(self._effect_combo.count()):
            if self._effect_combo.itemData(index) == kind:
                return index
        return 0

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
            self._clear_autosave()
            event.accept()
        else:
            event.ignore()
