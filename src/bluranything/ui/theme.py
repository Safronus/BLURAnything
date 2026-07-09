"""Dark, macOS-like appearance for the whole application.

macOS is the primary target, so the look mimics the system dark appearance:
near-black window chrome, subtly lighter controls, rounded corners and the
system accent blue. Applied through a Fusion palette plus a stylesheet so it
renders the same on every platform.
"""

from __future__ import annotations

from PySide6.QtGui import QColor, QFont, QPalette
from PySide6.QtWidgets import QApplication

ACCENT = "#0A84FF"
WINDOW_BG = "#1E1E1E"
BASE_BG = "#161616"
CONTROL_BG = "#2C2C2E"
CONTROL_HOVER = "#3A3A3C"
BORDER = "#3A3A3C"
TEXT = "#ECECEC"
TEXT_MUTED = "#9A9A9E"

_STYLESHEET = f"""
QWidget {{
    background-color: {WINDOW_BG};
    color: {TEXT};
    font-size: 13px;
}}
QMainWindow, QDialog {{ background-color: {WINDOW_BG}; }}
QToolBar {{
    background-color: {WINDOW_BG};
    border: none;
    border-bottom: 1px solid {BORDER};
    spacing: 6px;
    padding: 6px 8px;
}}
QToolButton, QPushButton {{
    background-color: {CONTROL_BG};
    border: 1px solid {BORDER};
    border-radius: 6px;
    padding: 5px 12px;
}}
QToolButton:hover, QPushButton:hover {{ background-color: {CONTROL_HOVER}; }}
QToolButton:pressed, QPushButton:pressed {{ background-color: {ACCENT}; }}
QToolButton:checked {{ background-color: {ACCENT}; border-color: {ACCENT}; }}
QToolButton:disabled, QPushButton:disabled {{ color: {TEXT_MUTED}; background-color: {WINDOW_BG}; }}
QMenuBar {{ background-color: {WINDOW_BG}; }}
QMenuBar::item:selected {{ background-color: {CONTROL_HOVER}; border-radius: 4px; }}
QMenu {{
    background-color: {CONTROL_BG};
    border: 1px solid {BORDER};
    border-radius: 8px;
    padding: 4px;
}}
QMenu::item {{ padding: 5px 24px; border-radius: 4px; }}
QMenu::item:selected {{ background-color: {ACCENT}; }}
QLabel {{ background: transparent; color: {TEXT_MUTED}; }}
QComboBox, QSpinBox {{
    background-color: {CONTROL_BG};
    border: 1px solid {BORDER};
    border-radius: 6px;
    padding: 4px 8px;
}}
QComboBox QAbstractItemView {{
    background-color: {CONTROL_BG};
    border: 1px solid {BORDER};
    selection-background-color: {ACCENT};
}}
QCheckBox {{ color: {TEXT}; spacing: 6px; }}
QSlider::groove:horizontal {{ height: 4px; background: {BORDER}; border-radius: 2px; }}
QSlider::handle:horizontal {{
    background: {TEXT};
    width: 14px; height: 14px;
    margin: -6px 0; border-radius: 7px;
}}
QSlider::sub-page:horizontal {{ background: {ACCENT}; border-radius: 2px; }}
QStatusBar {{ background-color: {WINDOW_BG}; color: {TEXT_MUTED}; border-top: 1px solid {BORDER}; }}
QSplitter::handle {{ background-color: {BORDER}; }}
QToolTip {{
    background-color: {CONTROL_BG}; color: {TEXT};
    border: 1px solid {BORDER}; padding: 4px;
}}
"""


def _palette() -> QPalette:
    palette = QPalette()
    palette.setColor(QPalette.ColorRole.Window, QColor(WINDOW_BG))
    palette.setColor(QPalette.ColorRole.WindowText, QColor(TEXT))
    palette.setColor(QPalette.ColorRole.Base, QColor(BASE_BG))
    palette.setColor(QPalette.ColorRole.AlternateBase, QColor(CONTROL_BG))
    palette.setColor(QPalette.ColorRole.Text, QColor(TEXT))
    palette.setColor(QPalette.ColorRole.Button, QColor(CONTROL_BG))
    palette.setColor(QPalette.ColorRole.ButtonText, QColor(TEXT))
    palette.setColor(QPalette.ColorRole.Highlight, QColor(ACCENT))
    palette.setColor(QPalette.ColorRole.HighlightedText, QColor("#FFFFFF"))
    palette.setColor(QPalette.ColorRole.ToolTipBase, QColor(CONTROL_BG))
    palette.setColor(QPalette.ColorRole.ToolTipText, QColor(TEXT))
    disabled = QColor(TEXT_MUTED)
    for role in (
        QPalette.ColorRole.WindowText,
        QPalette.ColorRole.Text,
        QPalette.ColorRole.ButtonText,
    ):
        palette.setColor(QPalette.ColorGroup.Disabled, role, disabled)
    return palette


def apply_theme(app: QApplication) -> None:
    """Apply the dark macOS-like theme to *app*."""
    app.setStyle("Fusion")
    app.setPalette(_palette())
    app.setStyleSheet(_STYLESHEET)
    # System UI font on macOS; harmless fallback elsewhere.
    app.setFont(QFont(app.font().family(), 13))
