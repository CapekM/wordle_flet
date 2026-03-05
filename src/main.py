import flet as ft


def main(page: ft.Page) -> None:
    page.title = "Wordle App"
    page.horizontal_alignment = ft.CrossAxisAlignment.CENTER
    page.vertical_alignment = ft.MainAxisAlignment.START

    word_list: list[str] = ["apple", "melon", "peach", "ppppp"]  # TODO better word list
    secret_word = "peach"  # TODO random.choice(word_list)
    max_attempts = 6

    current_attempt = 0
    game_over = False

    def evaluate_guess(guess: str) -> list[tuple[str, ft.Colors]]:
        """Return list of (letter, color) tuples."""
        colors: list[ft.Colors | None] = [None] * 5
        remaining: dict[str, int] = {}

        # Pass 1: greens — tally unmatched secret letters
        for i, letter in enumerate(guess):
            if letter == secret_word[i]:
                colors[i] = ft.Colors.GREEN
            else:
                remaining[secret_word[i]] = remaining.get(secret_word[i], 0) + 1

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

    def show_dialog(title: str, message: str) -> None:
        page.show_dialog(
            ft.AlertDialog(
                title=ft.Text(title),
                content=ft.Text(message),
            )
        )

    def check_guess_submit(e: ft.Event[ft.TextField]) -> None:
        check_guess()

    def check_guess_click(e: ft.Event[ft.Button]) -> None:
        check_guess()

    def check_guess() -> None:
        nonlocal current_attempt, game_over

        if game_over:
            return

        guess = input_field.value.strip().lower()
        input_field.value = ""

        if len(guess) != 5:
            show_dialog("Invalid Guess", "Please enter a 5-letter word.")
            return

        if guess not in word_list:
            show_dialog("Invalid Word", "This word is not in the list.")
            return

        current_attempt += 1

        letter_results = evaluate_guess(guess)
        spans = [
            ft.TextSpan(
                text=letter.upper(),
                style=ft.TextStyle(color=color, weight=ft.FontWeight.BOLD, size=20),
            )
            for letter, color in letter_results
        ]
        attempts_column.controls.append(ft.Text(spans=spans, size=20))
        attempts_column.update()

        win = guess == secret_word
        if win or current_attempt >= max_attempts:
            if win:
                result_text.value = f"Congratulations! You guessed: {secret_word}"
                result_text.color = ft.Colors.GREEN
            else:
                result_text.value = f"You lost! The word was: {secret_word}"
                result_text.color = ft.Colors.RED

            game_over = True
            input_field.disabled = True
            submit_button.disabled = True
            input_field.update()
            submit_button.update()
            result_text.update()
            return

        result_text.value = f"Attempt {current_attempt} of {max_attempts}"
        result_text.color = ft.Colors.WHITE
        result_text.update()

    input_field = ft.TextField(
        hint_text="Enter your 5-letter guess",
        max_length=5,
        on_submit=check_guess_submit,
        text_align=ft.TextAlign.CENTER,
        width=260,
    )

    attempts_column = ft.Column(
        horizontal_alignment=ft.CrossAxisAlignment.CENTER,
        spacing=4,
    )

    submit_button = ft.Button(
        content=ft.Text("Submit Guess"),
        on_click=check_guess_click,
    )

    result_text = ft.Text("", size=16)

    page.add(
        ft.SafeArea(
            expand=True,
            content=ft.Column(
                expand=True,
                controls=[
                    ft.Text("Wordle", size=32, weight=ft.FontWeight.BOLD),
                    attempts_column,
                    input_field,
                    submit_button,
                    result_text,
                ],
                horizontal_alignment=ft.CrossAxisAlignment.CENTER,
                spacing=16,
            ),
        )
    )


ft.run(main)
