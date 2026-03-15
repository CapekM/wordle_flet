from collections.abc import Callable

import flet as ft

# Storage keys
_KEY_DARK_MODE = "settings.dark_mode"
_KEY_SOUND = "settings.sound"


class SettingsScreen(ft.Column):
    """Settings screen with dark mode and sound toggles."""

    def __init__(self, on_back: Callable[[], None]) -> None:
        self._on_back = on_back

        self._dark_switch = ft.Switch(on_change=self._on_dark_mode_change)
        self._sound_switch = ft.Switch(on_change=self._on_sound_change)

        header = ft.Row(
            controls=[
                ft.IconButton(
                    icon=ft.Icons.ARROW_BACK,
                    on_click=lambda _: self._on_back(),
                    tooltip="Back to menu",
                ),
                ft.Text("Settings", size=24, weight=ft.FontWeight.BOLD),
            ],
            vertical_alignment=ft.CrossAxisAlignment.CENTER,
            spacing=8,
        )

        dark_row = _setting_row(
            icon=ft.Icons.DARK_MODE,
            label="Dark mode",
            description="Switch between light and dark theme",
            control=self._dark_switch,
        )

        sound_row = _setting_row(
            icon=ft.Icons.VOLUME_UP,
            label="Sound",
            description="Sound effects (coming soon)",
            control=self._sound_switch,
        )

        super().__init__(
            controls=[
                header,
                ft.Divider(),
                dark_row,
                ft.Divider(height=1, color=ft.Colors.GREY_300),
                sound_row,
            ],
            spacing=4,
            expand=True,
        )

    def did_mount(self) -> None:
        """Create the SharedPreferences service and kick off async settings loading."""
        assert isinstance(self.page, ft.Page)
        self._sp = ft.SharedPreferences()
        self.page.run_task(self._load_settings)

    async def _load_settings(self) -> None:
        """Load persisted settings from shared preferences."""
        assert isinstance(self.page, ft.Page)
        dark = await self._sp.get(_KEY_DARK_MODE)
        sound = await self._sp.get(_KEY_SOUND)

        self._dark_switch.value = (
            (dark == "true") if dark is not None else (self.page.platform_brightness == ft.Brightness.DARK)
        )
        self._sound_switch.value = (sound != "false") if sound is not None else True

        # Apply stored theme immediately
        if self.page.theme_mode != ft.ThemeMode.SYSTEM:
            self.page.theme_mode = ft.ThemeMode.DARK if self._dark_switch.value else ft.ThemeMode.LIGHT
        self.page.update()

    async def _on_dark_mode_change(self, e: ft.Event[ft.Switch]) -> None:
        assert isinstance(self.page, ft.Page)
        enabled: bool = bool(e.control.value)
        self.page.theme_mode = ft.ThemeMode.DARK if enabled else ft.ThemeMode.LIGHT
        await self._sp.set(_KEY_DARK_MODE, "true" if enabled else "false")
        self.page.update()

    async def _on_sound_change(self, e: ft.Event[ft.Switch]) -> None:
        enabled: bool = bool(e.control.value)
        await self._sp.set(_KEY_SOUND, "true" if enabled else "false")


def _setting_row(
    icon: ft.IconData,
    label: str,
    description: str,
    control: ft.Control,
) -> ft.Row:
    """Build a single settings row: icon + text on the left, control on the right."""
    return ft.Row(
        controls=[
            ft.Icon(icon, size=24),
            ft.Column(
                controls=[
                    ft.Text(label, size=16, weight=ft.FontWeight.W_600),
                    ft.Text(description, size=12, color=ft.Colors.GREY_500),
                ],
                spacing=2,
                expand=True,
            ),
            control,
        ],
        vertical_alignment=ft.CrossAxisAlignment.CENTER,
        spacing=12,
    )
