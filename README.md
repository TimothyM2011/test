# RightSide

A right-edge auto-hide sidebar for Windows. Dark mode only, local-only,
config-driven, plugin-style modules.

## What this build adds (Dispatch 1)

- **Module framework** — `core/module.py` defines a `Module` base class.
  `core/window.py` now reads `config.json > modules` and instantiates each
  module in order instead of hard-coding the hardware card.
- **Persistence** — `core/state.py` writes atomic JSON under `state/` with
  a debounced saver so typing in a note doesn't hammer the disk.
- **Notes** — a named list of notes. Click one to edit. Add/delete/rename.
- **Tasks** — checkbox list with optional due dates. Overdue-and-unchecked
  tasks turn red and sort to the top.
- **Clock** — one module, two modes: Timer and Stopwatch. Timers resume
  across app restarts by storing wall-clock time, not tick counts.
- **Expand to 600px** — clicking a module's expand chevron widens the whole
  sidebar from 300px to 600px with a smooth animation. Collapsing the last
  expanded module animates back.

## Architecture

```

RightSide/
├── main.py
├── config.json
├── requirements.txt
├── core/
│   ├── config.py          # loads config.json with defaults
│   ├── theme.py           # single source of truth for colors
│   ├── widgets.py         # Card, MetricRow, ExpandedCard, IconButton
│   ├── tick_dispatcher.py # one shared timer, two tiers
│   ├── edge_trigger.py    # DPI-aware hysteresis + cooldown
│   ├── module.py          # Module base class
│   ├── state.py           # atomic JSON persistence + debounce
│   ├── window.py          # the frameless always-on-top sidebar
│   └── tray.py            # tray icon + Quit
└── modules/
├── hardware/
│   └── hardware.py    # psutil + pynvml
├── notes/
│   └── notes.py       # named notes, editor
├── tasks/
│   └── tasks.py       # checkbox list, due dates
└── timers/
└── clock.py       # Timer + Stopwatch

```

## Install

```bash
python -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt
python main.py
```

Move the mouse to the right edge of the primary monitor. The sidebar
slides in. Move away and it slides out after a short grace period.

Right-click the tray icon → Quit.

## Adding a new module

1. Create `modules/<name>/<name>.py`.
2. Subclass `core.module.Module`, implement `id`, `title`, `build_widget()`.
3. Add `<name>` to `config.json > modules`.

State for the module will live at `state/<name>.json` automatically.

## Tunables (config.json)

| Key ↕▾ | Default ↕▾ | Meaning ↕▾ |
|---|---|---|
| −`sidebar_width` | 300 | width in logical px |
| −`expanded_width` | 600 | width when a module is expanded |
| `anim_ms` | 180 | slide duration |
| `edge_trigger_px` | 3 | width of the trigger band, in physical px |
| `leave_grace_ms` | 350 | cursor must be away this long before closing |
| `reopen_cooldown_ms` | 450 | wait after closing before reopening |
| `poll_ms` | 100 | edge poll interval |
| `debug_edge` | false | print cursor/screen math once per poll |
⚙

## Roadmap

- Dispatch 2: apps launcher, clipboard history, weather
- Dispatch 3: laptop specs via WMI, system controls
- Customize editor UI
- Plugin discovery (auto-load any folder under `modules/`)
- CPU / GPU temperatures via LibreHardwareMonitor

</BDS:create_file>

<BDS:create_file fileName="requirements.txt">

```text
PySide6>=6.6
psutil>=5.9
pynvml>=11.5 ; platform_system == "Windows"

