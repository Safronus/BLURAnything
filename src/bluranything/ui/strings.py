"""User-facing strings in Czech.

Centralised here so the UI reads in one language today and can be localised
(e.g. via Qt translations) later without hunting strings across the code.
"""

from __future__ import annotations

APP_TITLE = "BLURAnything"  # brand name, not translated

# --- Menus ---
MENU_FILE = "&Soubor"
MENU_EDIT = "Úprav&y"
MENU_HELP = "Nápo&věda"

# --- Actions ---
ACTION_OPEN = "&Otevřít…"
ACTION_PASTE = "&Vložit"
ACTION_SAVE = "&Uložit…"
ACTION_COPY = "&Kopírovat výsledek"
ACTION_CLEAR = "Vy&mazat vše"
ACTION_UNDO = "&Zpět"
ACTION_REDO = "Zn&ovu"
ACTION_QUIT = "&Konec"
ACTION_ABOUT = "O aplikaci BLURAnything"

# --- Tool names (also used as toolbar combo entries) ---
TOOL_RECTANGLE = "Obdélník"
TOOL_ELLIPSE = "Elipsa"
TOOL_POLYGON = "Mnohoúhelník"
TOOL_LASSO = "Laso"
TOOL_BRUSH = "Štětec"

# --- Effect names + intensity-slider captions ---
EFFECT_BLUR = "Rozostření"
EFFECT_PIXELATE = "Pixelizace"
EFFECT_SOLID = "Výplň"
CAPTION_BLUR = "Rozostření"
CAPTION_PIXEL_SIZE = "Velikost bloku"
CAPTION_SOLID = "Výplň"

# --- Other control captions ---
LABEL_FEATHER = "Prolnutí"
LABEL_BRUSH = "Štětec"
CHECK_SOFT_EDGES = "Měkké okraje"

# --- Canvas / preview ---
PLACEHOLDER_EDITOR = "Otevřete, vložte (⌘V) nebo přetáhněte obrázek"
PLACEHOLDER_PREVIEW = "Náhled"
DROP_HINT = "Přetažením otevřete obrázek"

# --- Tool hints (status bar) ---
TOOL_HINT_RECTANGLE = "Obdélník — tažením rozmažete oblast."
TOOL_HINT_ELLIPSE = "Elipsa — tažením rozmažete oválnou oblast."
TOOL_HINT_POLYGON = "Mnohoúhelník — klikáním přidávejte body, dvojklikem uzavřete."
TOOL_HINT_LASSO = "Laso — tažením nakreslete volnou oblast."
TOOL_HINT_BRUSH = "Štětec — tažením malujte rozostření."

# --- Status messages ---
STATUS_WELCOME = "Otevřete nebo vložte obrázek (⌘V), pak tažením rozmažte."
STATUS_COPIED = "Výsledek zkopírován do schránky"
STATUS_RECOVERED = "Obnovena neuložená práce"


def status_opened(name: str, width: int, height: int) -> str:
    return f"Otevřeno: {name} ({width}×{height})"


def status_pasted(width: int, height: int) -> str:
    return f"Vložený obrázek ({width}×{height})"


def status_saved(name: str) -> str:
    return f"Uloženo: {name}"


# --- Dialogs ---
DIALOG_OPEN_TITLE = "Otevřít obrázek"
DIALOG_SAVE_TITLE = "Uložit obrázek"
DISCARD_QUESTION = "Máte neuložené změny. Zahodit je?"
PASTE_NO_IMAGE = "Ve schránce není žádný obrázek."
RECOVERY_QUESTION = "Obnovit neuloženou práci z minulého sezení?"
FILTER_IMAGES = "Obrázky"


def open_error(path: object, exc: object) -> str:
    return f"Soubor {path} se nepodařilo otevřít:\n{exc}"


def save_error(path: object, exc: object) -> str:
    return f"Soubor {path} se nepodařilo uložit:\n{exc}"


# --- Window title fragments ---
TITLE_NO_IMAGE = "žádný obrázek"
TITLE_PASTED = "vložený obrázek"

# --- About box ---
ABOUT_TAGLINE = "Rozmažte citlivé části obrázků a screenshotů."
