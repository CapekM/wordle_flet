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

# Tile flip-reveal animation timing.
# FLIP_DURATION_MS: how long each half-flip (out or in) takes.
# TILE_STAGGER_MS:  delay before the next tile starts its flip.
# With both equal the tiles reveal sequentially with no overlap.
FLIP_DURATION_MS: int = 200
TILE_STAGGER_MS: int = 200
