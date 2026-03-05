import flet as ft

from game import WordleGame


def main(page: ft.Page) -> None:
    page.title = "Wordle App"
    page.horizontal_alignment = ft.CrossAxisAlignment.CENTER
    page.vertical_alignment = ft.MainAxisAlignment.START

    game = WordleGame()
    page.add(ft.SafeArea(expand=True, content=game))


ft.run(main)
