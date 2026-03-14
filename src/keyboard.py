import flet as ft

# ---------------------------------------------------------------------------
# Layout
# ---------------------------------------------------------------------------

# Keys with "/" denote two coupled variants (base / diacritic).
# Pressing a coupled key when the last typed character is the base letter
# toggles it to the diacritic variant.
KEYBOARD_ROWS: list[list[str]] = [
    ["Ú/Ů", "Č", "Ě", "Ř", "Š", "Ž"],
    ["W", "E/É", "R", "T/Ť", "Y/Ý", "U", "I/Í", "O/Ó", "P"],
    ["A/Á", "S", "D/Ď", "F", "G", "H", "J", "K", "L"],
    ["Z", "X", "C", "V", "B", "M", "N/Ň", "<-"],
]

# Derived once at import time.
COUPLE_LETTERS: list[tuple[str, str]] = [
    (key[0].lower(), key[2].lower()) for row in KEYBOARD_ROWS for key in row if "/" in key
]

# ---------------------------------------------------------------------------
# Colours
# ---------------------------------------------------------------------------

DEFAULT_BG = ft.Colors.GREY_300
DEFAULT_FG = ft.Colors.BLACK

# Higher value = higher priority; a key never downgrades to a lower tier.
COLOR_PRIORITY: dict[ft.Colors, int] = {
    ft.Colors.GREEN: 2,
    ft.Colors.ORANGE_300: 1,
    ft.Colors.GREY_700: 0,
}

# ---------------------------------------------------------------------------
# KeyboardKey
# ---------------------------------------------------------------------------


class KeyboardKey(ft.Button):
    """A single key on the on-screen Czech keyboard."""

    def __init__(self, label: str, on_press: ft.ControlEventHandler) -> None:
        self._label = label
        self._hint_color: ft.Colors | None = None
        self._label_text = ft.Text(
            label,
            size=12,
            weight=ft.FontWeight.W_600,
            color=DEFAULT_FG,
        )
        super().__init__(
            content=self._label_text,
            on_click=on_press,
            style=ft.ButtonStyle(
                bgcolor=DEFAULT_BG,
                padding=ft.padding.symmetric(horizontal=2, vertical=4),
                shape=ft.RoundedRectangleBorder(radius=4),
            ),
            width=52 if label == "<-" else 34,
            height=46,
        )

    @property
    def label(self) -> str:
        return self._label

    def apply_hint(self, color: ft.Colors) -> None:
        """Update key colour following green > orange > grey priority."""
        current_priority = COLOR_PRIORITY.get(
            self._hint_color if self._hint_color is not None else ft.Colors.GREY_300, -1
        )
        new_priority = COLOR_PRIORITY.get(color, -1)
        if new_priority <= current_priority:
            return
        self._hint_color = color
        assert self.style is not None
        self.style.bgcolor = color
        self._label_text.color = ft.Colors.WHITE
        self.update()

    def reset(self) -> None:
        self._hint_color = None
        assert self.style is not None
        self.style.bgcolor = DEFAULT_BG
        self._label_text.color = DEFAULT_FG
        self.update()


# ---------------------------------------------------------------------------
# Key-press logic (pure, no UI side-effects)
# ---------------------------------------------------------------------------


def apply_key_to_guess(guess: str, label: str, word_len: int) -> str:
    """Return the updated guess string after pressing *label*.

    Implements the coupled-letter toggle logic from old_wordle.py:
    - "<-"  → backspace
    - "X/Y" → if last char is base X, toggle to variant Y; else append X (if room)
    - plain → append lowercased letter (if room)
    """
    if label == "<-":
        return guess[:-1] if guess else guess

    if "/" in label:
        base = label[0].lower()
        variant = label[2].lower()
        last = guess[-1] if guess else ""
        if last == base:
            return guess[:-1] + variant
        if len(guess) < word_len:
            return guess + base
        return guess

    if len(guess) < word_len:
        return guess + label.lower()

    return guess
