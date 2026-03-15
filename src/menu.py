from collections.abc import Callable

import flet as ft


class MainMenu(ft.Column):
    """Main menu screen shown at app startup."""

    def __init__(self, on_play: Callable[[], None], on_settings: Callable[[], None]) -> None:
        self._on_play = on_play
        self._on_settings = on_settings

        play_button = ft.Button(
            content=ft.Text("Play", size=18, weight=ft.FontWeight.BOLD, color=ft.Colors.WHITE),
            on_click=self._on_play,
            style=ft.ButtonStyle(
                bgcolor=ft.Colors.GREEN_600,
                padding=ft.Padding.symmetric(horizontal=48, vertical=16),
                shape=ft.RoundedRectangleBorder(radius=8),
            ),
            height=56,
            width=200,
        )

        settings_button = ft.Button(
            content=ft.Text("Settings", size=18, weight=ft.FontWeight.BOLD, color=ft.Colors.WHITE),
            on_click=self._on_settings,
            style=ft.ButtonStyle(
                bgcolor=ft.Colors.BLUE_GREY_600,
                padding=ft.Padding.symmetric(horizontal=48, vertical=16),
                shape=ft.RoundedRectangleBorder(radius=8),
            ),
            height=56,
            width=200,
        )

        super().__init__(
            controls=[
                ft.Text("Wordle", size=52, weight=ft.FontWeight.BOLD),
                ft.Text("Guess the Czech word", size=16, color=ft.Colors.GREY_500),
                ft.Container(height=32),
                play_button,
                ft.Container(height=12),
                settings_button,
            ],
            horizontal_alignment=ft.CrossAxisAlignment.CENTER,
            alignment=ft.MainAxisAlignment.CENTER,
            expand=True,
            spacing=0,
        )
