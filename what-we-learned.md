# What We Learned from Flet

## Core Concepts

- App entry point with `ft.run(main)` and `Page` configuration
- Custom control subclassing (`ft.Column`, `ft.Button`)
- Imperative update model (`control.update()`, `page.update()`)
- Lifecycle hooks (`did_mount()`)

## Layout & UI

- Layout containers: `Column`, `Row`, `Container`, `SafeArea`
- Display controls: `Text`, `Icon`, `Divider`
- Input controls: `Button`, `IconButton`, `Switch`
- Feedback: `SnackBar`, `AlertDialog`
- Styling: `ButtonStyle`, `Border`, `Padding`, `Alignment`, `Colors`, `FontWeight`, state-dependent colors via `ControlState`

## Navigation

- Manual view-stack navigation (`page.views` push/pop)
- Back-button handling (`page.on_view_pop`)

## Animations

- Implicit animations (`animate`, `animate_scale`)
- `ft.Animation` with curves and durations
- Staggered sequential animations via `asyncio.sleep()`

## Async & State

- `page.run_task()` to launch coroutines from sync handlers
- `async def` event handlers
- `ft.SharedPreferences` for persistent key-value storage

## Theming & Mobile

- `ThemeMode` (dark/light/system), `platform_brightness`
- `SafeArea` for device notches
- `pyproject.toml` `[tool.flet]` packaging config
