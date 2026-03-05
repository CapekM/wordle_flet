import flet as ft


class WordleGame(ft.Column):
    WORD_LIST: list[str] = ["apple", "melon", "peach", "ppppp"]  # TODO better word list
    SECRET_WORD: str = "peach"  # TODO random.choice(WORD_LIST)
    MAX_ATTEMPTS: int = 6

    def __init__(self) -> None:
        super().__init__(
            horizontal_alignment=ft.CrossAxisAlignment.CENTER,
            spacing=16,
            expand=True,
        )
        self._setup()

    def _setup(self) -> None:
        """Initialise game state and build the control tree."""
        self.word_list = self.WORD_LIST
        self.secret_word = self.SECRET_WORD
        self.max_attempts = self.MAX_ATTEMPTS

        self.current_attempt: int = 0
        self.game_over: bool = False

        self._attempts_column = ft.Column(
            horizontal_alignment=ft.CrossAxisAlignment.CENTER,
            spacing=4,
        )
        self._input_field = ft.TextField(
            hint_text="Enter your 5-letter guess",
            max_length=5,
            on_submit=self._on_submit,
            text_align=ft.TextAlign.CENTER,
            width=260,
        )
        self._submit_button = ft.Button(
            content=ft.Text("Submit Guess"),
            on_click=self._on_click,
        )
        self._play_again_button = ft.Button(
            content=ft.Text("Play Again"),
            on_click=self._on_play_again_click,
            visible=False,
        )
        self._result_text = ft.Text("", size=16)

        self.controls = [
            ft.Text("Wordle", size=32, weight=ft.FontWeight.BOLD),
            self._attempts_column,
            self._input_field,
            self._submit_button,
            self._play_again_button,
            self._result_text,
        ]

    def _on_submit(self, e: ft.Event[ft.TextField]) -> None:
        self._check_guess()

    def _on_click(self, e: ft.Event[ft.Button]) -> None:
        self._check_guess()

    def _on_play_again_click(self, e: ft.Event[ft.Button]) -> None:
        self._setup()

    def _show_dialog(self, title: str, message: str) -> None:
        self.page.show_dialog(  # type: ignore[union-attr]
            ft.AlertDialog(
                title=ft.Text(title),
                content=ft.Text(message),
            )
        )

    def _evaluate_guess(self, guess: str) -> list[tuple[str, ft.Colors]]:
        """Return list of (letter, color) tuples."""
        colors: list[ft.Colors | None] = [None] * 5
        remaining: dict[str, int] = {}

        # Pass 1: greens — tally unmatched secret letters
        for i, letter in enumerate(guess):
            if letter == self.secret_word[i]:
                colors[i] = ft.Colors.GREEN
            else:
                remaining[self.secret_word[i]] = remaining.get(self.secret_word[i], 0) + 1

        # Pass 2: oranges / reds
        for i, letter in enumerate(guess):
            if colors[i] is not None:
                continue
            if remaining.get(letter, 0) > 0:
                colors[i] = ft.Colors.ORANGE
                remaining[letter] -= 1
            else:
                colors[i] = ft.Colors.RED

        return [(letter, colors[i]) for i, letter in enumerate(guess)]  # type: ignore[misc]

    def _check_guess(self) -> None:
        if self.game_over:
            return

        guess = self._input_field.value.strip().lower()
        self._input_field.value = ""

        if len(guess) != 5:
            self._show_dialog("Invalid Guess", "Please enter a 5-letter word.")
            return

        if guess not in self.word_list:
            self._show_dialog("Invalid Word", "This word is not in the list.")
            return

        self.current_attempt += 1

        letter_results = self._evaluate_guess(guess)
        spans = [
            ft.TextSpan(
                text=letter.upper(),
                style=ft.TextStyle(color=color, weight=ft.FontWeight.BOLD, size=20),
            )
            for letter, color in letter_results
        ]
        self._attempts_column.controls.append(ft.Text(spans=spans, size=20))
        self._attempts_column.update()

        win = guess == self.secret_word
        if win or self.current_attempt >= self.max_attempts:
            if win:
                self._result_text.value = f"Congratulations! You guessed: {self.secret_word}"
                self._result_text.color = ft.Colors.GREEN
            else:
                self._result_text.value = f"You lost! The word was: {self.secret_word}"
                self._result_text.color = ft.Colors.RED

            self.game_over = True
            self._input_field.disabled = True
            self._submit_button.disabled = True
            self._play_again_button.visible = True
            self._input_field.update()
            self._submit_button.update()
            self._play_again_button.update()
            self._result_text.update()
            return

        self._result_text.value = f"Attempt {self.current_attempt} of {self.max_attempts}"
        self._result_text.color = ft.Colors.WHITE
        self._result_text.update()
