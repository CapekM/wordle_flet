import asyncio
import itertools
import random
from collections.abc import Callable

import flet as ft

from const import (
    FLIP_DURATION_MS,
    HINT_ABSENT,
    HINT_CORRECT,
    HINT_MISPLACED,
    MAX_ATTEMPTS,
    POP_DURATION_MS,
    POP_SCALE,
    TILE_SIZE,
    TILE_STAGGER_MS,
    WORD_LEN,
)
from keyboard import (
    COUPLE_LETTERS,
    KEYBOARD_ROWS,
    KeyboardKey,
    apply_key_to_guess,
)
from stats import GameStats, build_stats_dialog, load_stats, record_loss, record_win, save_stats
from words import WORD_LIST


class WordleGame(ft.Column):
    def __init__(self, on_home: Callable[[], None] | None = None) -> None:
        self._on_home = on_home
        self._stats = GameStats()
        self._sp: ft.SharedPreferences | None = None
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
        self.max_attempts = MAX_ATTEMPTS

        self.current_attempt: int = 0
        self.game_over: bool = False
        self._animating: bool = False
        self._current_guess: str = ""
        self._past_results: list[list[tuple[str, ft.Colors]]] = []

        grid_widget = self._build_grid()
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
                padding=ft.Padding.symmetric(horizontal=24, vertical=12),
                shape=ft.RoundedRectangleBorder(radius=6),
            ),
            height=48,
        )
        self._suggest_button = ft.Button(
            content=ft.Text("Suggest", color=ft.Colors.WHITE),
            on_click=self._on_suggest_click,
            style=ft.ButtonStyle(
                bgcolor=ft.Colors.ORANGE_700,
                padding=ft.Padding.symmetric(horizontal=24, vertical=12),
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
                padding=ft.Padding.symmetric(horizontal=24, vertical=12),
                shape=ft.RoundedRectangleBorder(radius=6),
            ),
            height=48,
        )
        self._result_text = ft.Text("", size=16)

        home_button = ft.IconButton(
            icon=ft.Icons.ARROW_BACK,
            on_click=lambda _: self._on_home() if self._on_home else None,
            tooltip="Back to menu",
            visible=self._on_home is not None,
        )
        stats_button = ft.IconButton(
            icon=ft.Icons.BAR_CHART,
            on_click=lambda _: self._show_stats_dialog(),
            tooltip="Statistics",
        )
        header = ft.Row(
            controls=[
                home_button,
                ft.Container(
                    content=ft.Text("Wordle", size=32, weight=ft.FontWeight.BOLD, text_align=ft.TextAlign.CENTER),
                    expand=True,
                    alignment=ft.Alignment(0, 0),
                ),
                stats_button,
            ],
            vertical_alignment=ft.CrossAxisAlignment.CENTER,
        )

        self.controls = [
            header,
            grid_widget,
            keyboard_widget,
            ft.Row(
                controls=[self._submit_button, self._suggest_button, self._play_again_button],
                alignment=ft.MainAxisAlignment.CENTER,
                spacing=12,
            ),
            self._result_text,
        ]

    def did_mount(self) -> None:
        """Load persisted statistics once the control is mounted."""
        assert isinstance(self.page, ft.Page)
        self._sp = ft.SharedPreferences()
        self.page.run_task(self._load_stats)

    async def _load_stats(self) -> None:
        assert self._sp is not None
        self._stats = await load_stats(self._sp)

    def _build_grid(self) -> ft.Column:
        """Build the full 6×5 guess grid; populates _grid_texts and _grid_boxes.

        All rows are visible from the start. The active cell (where the next
        letter will land) is shown with a darker border so the player always
        knows their current position. Row 0 / cell 0 starts as the active cell.
        """
        self._grid_texts: list[list[ft.Text]] = []
        self._grid_boxes: list[list[ft.Container]] = []

        rows: list[ft.Control] = []
        for row_idx in range(MAX_ATTEMPTS):
            row_texts: list[ft.Text] = []
            row_boxes: list[ft.Container] = []
            cells: list[ft.Control] = []
            for col_idx in range(WORD_LEN):
                txt = ft.Text(
                    "",
                    size=20,
                    weight=ft.FontWeight.BOLD,
                    color=ft.Colors.BLACK,
                )
                # First cell of the first row starts highlighted (active).
                is_active = row_idx == 0 and col_idx == 0
                box = ft.Container(
                    content=txt,
                    width=TILE_SIZE,
                    height=TILE_SIZE,
                    alignment=ft.Alignment(0, 0),
                    border=ft.Border.all(2, ft.Colors.YELLOW_700 if is_active else ft.Colors.GREY_400),
                    border_radius=4,
                    bgcolor=ft.Colors.WHITE,
                    animate=ft.Animation(FLIP_DURATION_MS, ft.AnimationCurve.EASE_IN),
                    scale=1.0,
                    animate_scale=ft.Animation(POP_DURATION_MS, ft.AnimationCurve.EASE_OUT),
                )
                row_texts.append(txt)
                row_boxes.append(box)
                cells.append(box)
            self._grid_texts.append(row_texts)
            self._grid_boxes.append(row_boxes)
            rows.append(
                ft.Row(
                    controls=cells,
                    alignment=ft.MainAxisAlignment.CENTER,
                    spacing=6,
                )
            )
        return ft.Column(
            controls=rows,
            spacing=6,
            horizontal_alignment=ft.CrossAxisAlignment.CENTER,
        )

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
        if self.game_over or self._animating:
            return
        old_guess = self._current_guess
        self._current_guess = apply_key_to_guess(self._current_guess, e.control.label, WORD_LEN)
        self._update_guess_display()

        # Pop the tile
        if self._current_guess != old_guess:
            pop_col = len(self._current_guess) - 1
            box = self._grid_boxes[self.current_attempt][pop_col]
            assert isinstance(self.page, ft.Page)
            self.page.run_task(self._pop_tile, box)

    async def _pop_tile(self, box: ft.Container) -> None:
        """Brief uniform scale-up then back to 1.0 — typewriter pop on letter entry."""
        box.animate_scale = ft.Animation(POP_DURATION_MS, ft.AnimationCurve.EASE_OUT)
        box.scale = POP_SCALE
        box.update()
        await asyncio.sleep(POP_DURATION_MS / 1_000)
        box.animate_scale = ft.Animation(POP_DURATION_MS, ft.AnimationCurve.EASE_IN)
        box.scale = 1.0
        box.update()

    def _update_guess_display(self) -> None:
        row = self.current_attempt
        n = len(self._current_guess)
        for i in range(WORD_LEN):
            txt = self._grid_texts[row][i]
            box = self._grid_boxes[row][i]
            txt.value = self._current_guess[i].upper() if i < n else ""
            # The next empty slot gets the yellow border; all others use default.
            box.border = ft.Border.all(2, ft.Colors.YELLOW_700 if i == n else ft.Colors.GREY_400)
            box.update()
        self._submit_button.disabled = n != WORD_LEN
        self._submit_button.update()

    def _on_submit_click(self, e: ft.Event[ft.Button]) -> None:
        self._check_guess()

    def _on_play_again_click(self, e: ft.Event[ft.Button]) -> None:
        self._setup()
        self.update()

    def _show_snackbar(self, message: str, color: ft.Colors = ft.Colors.WHITE) -> None:
        """Show a brief non-blocking notification at the bottom of the screen."""
        assert isinstance(self.page, ft.Page)
        snackbar = ft.SnackBar(
            content=ft.Text(message, color=color, weight=ft.FontWeight.W_500),
            duration=2000,
            open=True,
        )
        self.page.overlay.append(snackbar)
        self.page.update()

    def _show_stats_dialog(self, last_attempt: int | None = None) -> None:
        """Open the statistics dialog. Highlights *last_attempt* bar if provided."""
        assert isinstance(self.page, ft.Page)
        dialog = build_stats_dialog(self._stats, last_attempt=last_attempt)
        self.page.show_dialog(dialog)

    def _check_guess(self) -> None:
        if self.game_over or self._animating:
            return

        guess = self._current_guess.lower()

        if len(guess) != WORD_LEN:
            self._show_snackbar(f"Please enter a {WORD_LEN}-letter word.")
            return

        if not self._guess_in_word_list(guess):
            self._show_snackbar("This word is not in the word list.")
            return

        self._current_guess = ""
        attempt_row = self.current_attempt
        self.current_attempt += 1

        letter_results = self._evaluate_guess(guess)
        self._past_results.append(letter_results)

        self._animating = True
        self._submit_button.disabled = True
        self._submit_button.update()
        self.page.run_task(self._reveal_and_finish, attempt_row, letter_results, guess)

    async def _reveal_and_finish(
        self,
        attempt_row: int,
        letter_results: list[tuple[str, ft.Colors]],
        guess: str,
    ) -> None:
        """Animate the tile flip reveal, then handle win/loss logic."""
        for i, (letter, color) in enumerate(letter_results):
            box = self._grid_boxes[attempt_row][i]
            txt = self._grid_texts[attempt_row][i]

            # Phase 1 — flip out (height: TILE_SIZE → 0, EASE_IN)
            box.animate = ft.Animation(FLIP_DURATION_MS, ft.AnimationCurve.EASE_IN)
            box.height = 0
            box.update()
            await asyncio.sleep(FLIP_DURATION_MS / 1_000)

            # Midpoint — swap colours while invisible
            box.bgcolor = color
            box.border = None
            txt.color = ft.Colors.WHITE

            # Phase 2 — flip in (height: 0 → TILE_SIZE, EASE_OUT)
            box.animate = ft.Animation(FLIP_DURATION_MS, ft.AnimationCurve.EASE_OUT)
            box.height = TILE_SIZE
            box.update()

            # Apply keyboard hint as each tile reveals
            self._apply_key_hint(letter, color)

            # Stagger before next tile
            await asyncio.sleep(TILE_STAGGER_MS / 1_000)

        # Wait for last tile's flip-in to finish
        remaining = max(0.0, (FLIP_DURATION_MS - TILE_STAGGER_MS) / 1_000)
        if remaining > 0:
            await asyncio.sleep(remaining)

        # Win/loss logic
        win = guess == self.secret_word
        if win or self.current_attempt >= self.max_attempts:
            if win:
                self._result_text.value = f"Congratulations! You guessed: {self.secret_word}"
                self._result_text.color = ft.Colors.GREEN
                self._stats = record_win(self._stats, self.current_attempt)
            else:
                self._result_text.value = f"You lost! The word was: {self.secret_word}"
                self._result_text.color = ft.Colors.RED
                self._stats = record_loss(self._stats)

            if self._sp is not None:
                await save_stats(self._sp, self._stats)

            self.game_over = True
            self._submit_button.visible = False
            self._submit_button.update()
            self._suggest_button.visible = False
            self._suggest_button.update()
            self._play_again_button.visible = True
            self._play_again_button.update()
            self._result_text.update()

            # Brief pause before showing stats so the player sees the result.
            await asyncio.sleep(0.8)
            self._show_stats_dialog(
                last_attempt=self.current_attempt if win else None,
            )
        else:
            self._result_text.value = f"Attempt {self.current_attempt} of {self.max_attempts}"
            self._result_text.color = ft.Colors.WHITE
            self._result_text.update()
            self._update_guess_display()

        self._animating = False

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
                colors[i] = HINT_CORRECT
            else:
                remaining[self.secret_word[i]] = remaining.get(self.secret_word[i], 0) + 1

        # Pass 2: orange or grey
        for i, letter in enumerate(guess):
            if colors[i] is not None:
                continue
            if remaining.get(letter, 0) > 0:
                colors[i] = HINT_MISPLACED
                remaining[letter] -= 1
            else:
                colors[i] = HINT_ABSENT

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
                if color in (HINT_CORRECT, HINT_MISPLACED):
                    go_count[letter] = go_count.get(letter, 0) + 1
                elif color == HINT_ABSENT:
                    grey_letters.add(letter)

            for i, (letter, color) in enumerate(result):
                if color == HINT_CORRECT:
                    greens[i] = letter
                elif color == HINT_MISPLACED:
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
        if self._animating:
            return
        word = self._suggest_word()
        if word is None:
            self._show_snackbar("No matching word found.")
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
