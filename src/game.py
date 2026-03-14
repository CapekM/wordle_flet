import itertools
import random

import flet as ft

from keyboard import (
    COUPLE_LETTERS,
    KEYBOARD_ROWS,
    KeyboardKey,
    apply_key_to_guess,
)
from words import WORD_LEN, WORD_LIST


class WordleGame(ft.Column):
    MAX_ATTEMPTS: int = 6

    def __init__(self) -> None:
        super().__init__(
            horizontal_alignment=ft.CrossAxisAlignment.CENTER,
            spacing=16,
            expand=True,
        )
        self._setup()

    def _setup(self) -> None:
        """Initialise (or re-initialise) game state and rebuild the control tree."""
        self.word_list = WORD_LIST
        self.secret_word = random.choice(self.word_list)
        self.max_attempts = self.MAX_ATTEMPTS

        self.current_attempt: int = 0
        self.game_over: bool = False
        self._current_guess: str = ""
        self._past_results: list[list[tuple[str, ft.Colors]]] = []

        self._attempts_column = ft.Column(
            horizontal_alignment=ft.CrossAxisAlignment.CENTER,
            spacing=4,
        )
        self._guess_boxes = self._build_guess_boxes()
        self._keyboard_keys: dict[str, KeyboardKey] = {}
        keyboard_widget = self._build_keyboard()

        self._submit_button = ft.Button(
            content=ft.Text("Submit", color=ft.Colors.WHITE),
            on_click=self._on_submit_click,
            disabled=True,
            style=ft.ButtonStyle(
                bgcolor={
                    ft.ControlState.DISABLED: ft.Colors.GREY_400,
                    ft.ControlState.DEFAULT: ft.Colors.BLUE_600,
                },
                padding=ft.padding.symmetric(horizontal=24, vertical=12),
                shape=ft.RoundedRectangleBorder(radius=6),
            ),
            height=48,
        )
        self._suggest_button = ft.Button(
            content=ft.Text("Suggest", color=ft.Colors.WHITE),
            on_click=self._on_suggest_click,
            style=ft.ButtonStyle(
                bgcolor=ft.Colors.ORANGE_700,
                padding=ft.padding.symmetric(horizontal=24, vertical=12),
                shape=ft.RoundedRectangleBorder(radius=6),
            ),
            height=48,
        )
        self._play_again_button = ft.Button(
            content=ft.Text("Play Again", color=ft.Colors.WHITE),
            on_click=self._on_play_again_click,
            visible=False,
            style=ft.ButtonStyle(
                bgcolor=ft.Colors.GREEN_600,
                padding=ft.padding.symmetric(horizontal=24, vertical=12),
                shape=ft.RoundedRectangleBorder(radius=6),
            ),
            height=48,
        )
        self._result_text = ft.Text("", size=16)

        self.controls = [
            ft.Text("Wordle", size=32, weight=ft.FontWeight.BOLD),
            self._attempts_column,
            self._guess_boxes,
            keyboard_widget,
            ft.Row(
                controls=[self._submit_button, self._suggest_button, self._play_again_button],
                alignment=ft.MainAxisAlignment.CENTER,
                spacing=12,
            ),
            self._result_text,
        ]

    def _build_guess_boxes(self) -> ft.Row:
        """Return a Row of WORD_LEN letter-display boxes."""
        self._guess_box_texts: list[ft.Text] = [
            ft.Text("", size=22, weight=ft.FontWeight.BOLD, color=ft.Colors.BLACK) for _ in range(WORD_LEN)
        ]
        boxes: list[ft.Control] = [
            ft.Container(
                content=txt,
                width=48,
                height=48,
                alignment=ft.Alignment(0, 0),
                border=ft.border.all(2, ft.Colors.GREY_400),
                border_radius=4,
                bgcolor=ft.Colors.WHITE,
            )
            for txt in self._guess_box_texts
        ]
        return ft.Row(controls=boxes, alignment=ft.MainAxisAlignment.CENTER, spacing=6)

    def _build_keyboard(self) -> ft.Column:
        """Build the on-screen keyboard; populates self._keyboard_keys."""
        rows: list[ft.Control] = []
        for row_labels in KEYBOARD_ROWS:
            key_widgets: list[ft.Control] = []
            for label in row_labels:
                key = KeyboardKey(label=label, on_press=self._on_key_press)
                self._keyboard_keys[label] = key
                key_widgets.append(key)
            rows.append(
                ft.Row(
                    controls=key_widgets,
                    alignment=ft.MainAxisAlignment.CENTER,
                    spacing=4,
                )
            )
        return ft.Column(
            controls=rows,
            spacing=4,
            horizontal_alignment=ft.CrossAxisAlignment.CENTER,
        )

    def _on_key_press(self, e: ft.Event[KeyboardKey]) -> None:
        if self.game_over:
            return
        self._current_guess = apply_key_to_guess(self._current_guess, e.control.label, WORD_LEN)
        self._update_guess_display()

    def _update_guess_display(self) -> None:
        for i, txt in enumerate(self._guess_box_texts):
            txt.value = self._current_guess[i].upper() if i < len(self._current_guess) else ""
            txt.update()
        self._submit_button.disabled = len(self._current_guess) != WORD_LEN
        self._submit_button.update()

    def _on_submit_click(self, e: ft.Event[ft.Button]) -> None:
        self._check_guess()

    def _on_play_again_click(self, e: ft.Event[ft.Button]) -> None:
        self._setup()
        self.update()

    def _show_dialog(self, title: str, message: str) -> None:
        self.page.show_dialog(
            ft.AlertDialog(
                title=ft.Text(title),
                content=ft.Text(message),
            )
        )

    def _check_guess(self) -> None:
        if self.game_over:
            return

        guess = self._current_guess.lower()

        if len(guess) != WORD_LEN:
            self._show_dialog("Invalid Guess", f"Please enter a {WORD_LEN}-letter word.")
            return

        if not self._guess_in_word_list(guess):
            self._show_dialog("Invalid Word", "This word is not in the list.")
            return

        self._current_guess = ""
        self._update_guess_display()
        self.current_attempt += 1

        letter_results = self._evaluate_guess(guess)
        self._past_results.append(letter_results)
        spans = [
            ft.TextSpan(
                text=letter.upper(),
                style=ft.TextStyle(color=color, weight=ft.FontWeight.BOLD, size=20),
            )
            for letter, color in letter_results
        ]
        self._attempts_column.controls.append(ft.Text(spans=spans, size=20))
        self._attempts_column.update()

        for letter, color in letter_results:
            self._apply_key_hint(letter, color)

        win = guess == self.secret_word
        if win or self.current_attempt >= self.max_attempts:
            if win:
                self._result_text.value = f"Congratulations! You guessed: {self.secret_word}"
                self._result_text.color = ft.Colors.GREEN
            else:
                self._result_text.value = f"You lost! The word was: {self.secret_word}"
                self._result_text.color = ft.Colors.RED

            self.game_over = True
            self._submit_button.visible = False
            self._submit_button.update()
            self._suggest_button.visible = False
            self._suggest_button.update()
            self._play_again_button.visible = True
            self._play_again_button.update()
            self._result_text.update()
            return

        self._result_text.value = f"Attempt {self.current_attempt} of {self.max_attempts}"
        self._result_text.color = ft.Colors.WHITE
        self._result_text.update()

    def _guess_in_word_list(self, guess: str) -> bool:
        """Check whether the guess (or any coupled-letter variant) is in the word list.

        Mirrors check_guess_in_words from old_wordle.py.
        """
        couple_flat = {ch for pair in COUPLE_LETTERS for ch in pair}
        coupled_indices = [i for i, ch in enumerate(guess) if ch in couple_flat]

        for combo_len in range(len(coupled_indices) + 1):
            for indices in itertools.combinations(coupled_indices, combo_len):
                candidate = list(guess)
                for idx in indices:
                    candidate[idx] = _swap_coupled(guess[idx])
                if "".join(candidate) in self.word_list:
                    return True
        return False

    def _evaluate_guess(self, guess: str) -> list[tuple[str, ft.Colors]]:
        """Return (letter, colour) pairs using green / orange / grey."""
        colors: list[ft.Colors | None] = [None] * WORD_LEN
        remaining: dict[str, int] = {}

        # Pass 1: greens
        for i, letter in enumerate(guess):
            if letter == self.secret_word[i]:
                colors[i] = ft.Colors.GREEN
            else:
                remaining[self.secret_word[i]] = remaining.get(self.secret_word[i], 0) + 1

        # Pass 2: orange or grey
        for i, letter in enumerate(guess):
            if colors[i] is not None:
                continue
            if remaining.get(letter, 0) > 0:
                colors[i] = ft.Colors.ORANGE_300
                remaining[letter] -= 1
            else:
                colors[i] = ft.Colors.GREY_700

        # Every slot is filled by this point; walrus filters out the None type.
        return [(letter, c) for i, letter in enumerate(guess) if (c := colors[i]) is not None]

    def _apply_key_hint(self, letter: str, color: ft.Colors) -> None:
        """Apply a colour hint to the key that owns *letter*."""
        letter_lower = letter.lower()
        for label, key in self._keyboard_keys.items():
            if label == "<-":
                continue
            # A coupled key "E/É" covers both 'e' and 'é'
            key_chars = {c.lower() for c in label if c != "/"}
            if letter_lower in key_chars:
                key.apply_hint(color)
                return

    def _suggest_word(self) -> str | None:
        """Return a random word consistent with all past guess results.

        Derives three kinds of constraints from self._past_results:
        - greens:       word[i] must be a specific letter
        - orange_banned: letter must appear in the word, but not at these positions
        - counts:       for each letter, the word must contain at least N
                        occurrences; if the same letter also appeared grey in
                        that guess, exactly N occurrences are required
        """
        greens: dict[int, str] = {}
        orange_banned: dict[str, set[int]] = {}
        min_counts: dict[str, int] = {}
        exact_counts: dict[str, int] = {}

        for result in self._past_results:
            # Count green+orange occurrences per letter in this one guess
            go_count: dict[str, int] = {}
            grey_letters: set[str] = set()

            for letter, color in result:
                if color in (ft.Colors.GREEN, ft.Colors.ORANGE_300):
                    go_count[letter] = go_count.get(letter, 0) + 1
                elif color == ft.Colors.GREY_700:
                    grey_letters.add(letter)

            for i, (letter, color) in enumerate(result):
                if color == ft.Colors.GREEN:
                    greens[i] = letter
                elif color == ft.Colors.ORANGE_300:
                    orange_banned.setdefault(letter, set()).add(i)

            for letter, count in go_count.items():
                min_counts[letter] = max(min_counts.get(letter, 0), count)
                if letter in grey_letters:
                    # Grey alongside green/orange pins the exact count
                    exact_counts[letter] = max(exact_counts.get(letter, 0), count)

            for letter in grey_letters:
                if letter not in go_count:
                    # Pure grey: letter is not in the word at all
                    exact_counts[letter] = 0

        def matches(word: str) -> bool:
            for pos, letter in greens.items():
                if word[pos] != letter:
                    return False
            for letter, positions in orange_banned.items():
                if letter not in word:
                    return False
                for pos in positions:
                    if word[pos] == letter:
                        return False
            for letter, count in exact_counts.items():
                if word.count(letter) != count:
                    return False
            for letter, count in min_counts.items():
                if letter not in exact_counts and word.count(letter) < count:
                    return False
            return True

        candidates = [w for w in self.word_list if matches(w)]
        return random.choice(candidates) if candidates else None

    def _on_suggest_click(self, e: ft.Event[ft.Button]) -> None:
        word = self._suggest_word()
        if word is None:
            self._show_dialog("No suggestion", "No matching word found.")
            return
        self._current_guess = word
        self._update_guess_display()


def _swap_coupled(letter: str) -> str:
    """Return the partner letter in a coupled pair, or the letter itself."""
    for base, variant in COUPLE_LETTERS:
        if letter == base:
            return variant
        if letter == variant:
            return base
    return letter
