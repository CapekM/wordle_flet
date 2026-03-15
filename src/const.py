import flet as ft

# Game rules
WORD_LEN = 5
MAX_ATTEMPTS = 6

# Grid tile size (px)
TILE_SIZE = 44

# Hint colours — used on both grid tiles and keyboard keys.
HINT_CORRECT: ft.Colors = ft.Colors.GREEN
HINT_MISPLACED: ft.Colors = ft.Colors.ORANGE_300
HINT_ABSENT: ft.Colors = ft.Colors.GREY_700
