import flet as ft

from game import WordleGame
from menu import MainMenu
from settings import SettingsScreen


def _make_view(route: str, content: ft.Control) -> ft.View:
    return ft.View(
        route=route,
        controls=[ft.SafeArea(expand=True, content=content)],
        padding=ft.Padding.all(0),
        vertical_alignment=ft.MainAxisAlignment.START,
        horizontal_alignment=ft.CrossAxisAlignment.CENTER,
    )


def main(page: ft.Page) -> None:
    page.title = "Wordle App"
    page.horizontal_alignment = ft.CrossAxisAlignment.CENTER
    page.vertical_alignment = ft.MainAxisAlignment.START

    def go_back() -> None:
        if len(page.views) > 1:
            page.views.pop()
            page.update()

    def on_view_pop(e: ft.ViewPopEvent) -> None:
        go_back()

    def show_game() -> None:
        page.views.append(_make_view("/game", WordleGame(on_home=go_back)))
        page.update()

    def show_settings() -> None:
        page.views.append(_make_view("/settings", SettingsScreen(on_back=go_back)))
        page.update()

    page.on_view_pop = on_view_pop
    page.views.append(_make_view("/", MainMenu(on_play=show_game, on_settings=show_settings)))
    page.update()


ft.run(main)
