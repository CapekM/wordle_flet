"""Game statistics: data model, persistence, and dialog UI."""

import json
from dataclasses import dataclass, field
from typing import Any

import flet as ft

from const import MAX_ATTEMPTS

_STORAGE_KEY = "wordle.stats"


@dataclass
class GameStats:
    """Tracks cumulative game outcomes."""

    games_played: int = 0
    games_won: int = 0
    current_streak: int = 0
    max_streak: int = 0
    guess_distribution: list[int] = field(default_factory=lambda: [0] * MAX_ATTEMPTS)

    def win_pct(self) -> int:
        """Return win percentage as an integer 0-100."""
        if self.games_played == 0:
            return 0
        return round(self.games_won * 100 / self.games_played)


# ---------------------------------------------------------------------------
# Persistence helpers
# ---------------------------------------------------------------------------


async def load_stats(sp: ft.SharedPreferences) -> GameStats:
    """Deserialise stats from SharedPreferences (returns defaults on first run)."""
    raw = await sp.get(_STORAGE_KEY)
    if raw is None:
        return GameStats()
    try:
        data: dict[str, Any] = json.loads(raw)
        return GameStats(
            games_played=int(data.get("games_played", 0)),
            games_won=int(data.get("games_won", 0)),
            current_streak=int(data.get("current_streak", 0)),
            max_streak=int(data.get("max_streak", 0)),
            guess_distribution=[int(v) for v in data.get("guess_distribution", [0] * MAX_ATTEMPTS)],
        )
    except (json.JSONDecodeError, TypeError, ValueError):
        return GameStats()


async def save_stats(sp: ft.SharedPreferences, stats: GameStats) -> None:
    """Serialise stats to SharedPreferences as JSON."""
    data = {
        "games_played": stats.games_played,
        "games_won": stats.games_won,
        "current_streak": stats.current_streak,
        "max_streak": stats.max_streak,
        "guess_distribution": stats.guess_distribution,
    }
    await sp.set(_STORAGE_KEY, json.dumps(data))


# ---------------------------------------------------------------------------
# Pure update functions
# ---------------------------------------------------------------------------


def record_win(stats: GameStats, attempts: int) -> GameStats:
    """Return a new GameStats reflecting a win in *attempts* guesses (1-based)."""
    dist = list(stats.guess_distribution)
    dist[attempts - 1] += 1
    new_streak = stats.current_streak + 1
    return GameStats(
        games_played=stats.games_played + 1,
        games_won=stats.games_won + 1,
        current_streak=new_streak,
        max_streak=max(stats.max_streak, new_streak),
        guess_distribution=dist,
    )


def record_loss(stats: GameStats) -> GameStats:
    """Return a new GameStats reflecting a loss (streak resets)."""
    return GameStats(
        games_played=stats.games_played + 1,
        games_won=stats.games_won,
        current_streak=0,
        max_streak=stats.max_streak,
        guess_distribution=list(stats.guess_distribution),
    )


# ---------------------------------------------------------------------------
# Dialog UI
# ---------------------------------------------------------------------------


def _stat_box(value: int | str, label: str) -> ft.Column:
    """A single summary stat: large number above a small label."""
    return ft.Column(
        controls=[
            ft.Text(str(value), size=28, weight=ft.FontWeight.BOLD, text_align=ft.TextAlign.CENTER),
            ft.Text(label, size=10, text_align=ft.TextAlign.CENTER),
        ],
        horizontal_alignment=ft.CrossAxisAlignment.CENTER,
        spacing=2,
        expand=True,
    )


def _distribution_row(attempt: int, count: int, max_count: int, highlight: bool) -> ft.Row:
    """One row of the guess-distribution bar chart."""
    # Bar fills proportionally; minimum width so zero-counts are still visible.
    fraction = count / max_count if max_count > 0 else 0
    bar_width = max(18, fraction * 180)
    bar_color = ft.Colors.GREEN if highlight else ft.Colors.GREY_600
    return ft.Row(
        controls=[
            ft.Text(str(attempt), size=14, width=14, text_align=ft.TextAlign.CENTER),
            ft.Container(
                content=ft.Text(
                    str(count),
                    size=12,
                    color=ft.Colors.WHITE,
                    text_align=ft.TextAlign.RIGHT,
                    weight=ft.FontWeight.BOLD,
                ),
                bgcolor=bar_color,
                width=bar_width,
                padding=ft.Padding.symmetric(horizontal=6, vertical=2),
                border_radius=2,
                alignment=ft.Alignment(1, 0),
                animate=ft.Animation(300, ft.AnimationCurve.EASE_OUT),
            ),
        ],
        spacing=6,
        vertical_alignment=ft.CrossAxisAlignment.CENTER,
    )


def build_stats_dialog(
    stats: GameStats,
    last_attempt: int | None = None,
) -> ft.AlertDialog:
    """Build the statistics AlertDialog with summary numbers and bar chart.

    *last_attempt* (1-based) highlights the corresponding distribution bar
    when the player has just finished a game.
    """
    summary = ft.Row(
        controls=[
            _stat_box(stats.games_played, "Played"),
            _stat_box(stats.win_pct(), "Win %"),
            _stat_box(stats.current_streak, "Streak"),
            _stat_box(stats.max_streak, "Max"),
        ],
        alignment=ft.MainAxisAlignment.SPACE_EVENLY,
    )

    max_count = max(stats.guess_distribution) if stats.guess_distribution else 0
    bars = ft.Column(
        controls=[
            _distribution_row(
                attempt=i + 1,
                count=stats.guess_distribution[i],
                max_count=max_count,
                highlight=(last_attempt is not None and i + 1 == last_attempt),
            )
            for i in range(MAX_ATTEMPTS)
        ],
        spacing=4,
    )

    return ft.AlertDialog(
        title=ft.Text("Statistics", text_align=ft.TextAlign.CENTER),
        content=ft.Column(
            controls=[summary, ft.Divider(), bars],
            tight=True,
            spacing=12,
            horizontal_alignment=ft.CrossAxisAlignment.CENTER,
        ),
    )
