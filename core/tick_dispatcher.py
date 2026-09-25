"""
core/tick_dispatcher.py

Single centralized ticking system instead of every module running
its own QTimer/thread. Modules register an update callback plus how
often (in ticks) they want to run at each tier.

Two tiers:
  COLLAPSED - sidebar hidden. Base tick = 5 minutes. Only modules
              marked cheap=True run here (e.g. hardware summary via
              psutil). Everything else is skipped entirely.
  EXPANDED  - sidebar visible. Base tick = 1 second. Each module
              declares a multiple of the base tick to run at
              (e.g. GPU every 4 ticks = ~4s, CPU every tick = ~1s).

On expand, we force one immediate full refresh pass across every
registered module before switching to the expanded tier, so the
user always sees fresh numbers the moment the panel opens.
"""

from dataclasses import dataclass
from typing import Callable
from PySide6.QtCore import QObject, QTimer

COLLAPSED_INTERVAL_MS = 5 * 60 * 1000   # 5 minutes
EXPANDED_BASE_INTERVAL_MS = 1000        # 1 second


@dataclass
class ModuleReg:
    name: str
    callback: Callable[[], None]
    cheap: bool = False          # runs even while collapsed
    expanded_every: int = 1      # run every N expanded base-ticks


class TickDispatcher(QObject):
    def __init__(self, parent=None):
        super().__init__(parent)
        self._modules: list[ModuleReg] = []
        self._expanded_tick_count = 0
        self._is_expanded = False

        self._timer = QTimer(self)
        self._timer.timeout.connect(self._on_tick)
        self._set_collapsed_tier()

    def register(self, name: str, callback: Callable[[], None],
                 cheap: bool = False, expanded_every: int = 1):
        self._modules.append(ModuleReg(name, callback, cheap, expanded_every))

    def _set_collapsed_tier(self):
        self._is_expanded = False
        self._timer.setInterval(COLLAPSED_INTERVAL_MS)
        if not self._timer.isActive():
            self._timer.start()

    def _set_expanded_tier(self):
        self._is_expanded = True
        self._expanded_tick_count = 0
        self._timer.setInterval(EXPANDED_BASE_INTERVAL_MS)

    def on_expand(self):
        """Call the instant the sidebar starts opening."""
        self.force_full_refresh()
        self._set_expanded_tier()

    def on_collapse(self):
        self._set_collapsed_tier()

    def force_full_refresh(self):
        for mod in self._modules:
            mod.callback()

    def _on_tick(self):
        if not self._is_expanded:
            # Collapsed tier: only cheap modules run
            for mod in self._modules:
                if mod.cheap:
                    mod.callback()
            return

        # Expanded tier
        self._expanded_tick_count += 1
        for mod in self._modules:
            if self._expanded_tick_count % mod.expanded_every == 0:
                mod.callback()
