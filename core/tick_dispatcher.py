"""
core/tick_dispatcher.py

One shared timer, two tiers:
  COLLAPSED - 5 minute tick, only cheap modules run
  EXPANDED  - 1 second base tick, modules run every N ticks

On expand we do one immediate full refresh so the user sees fresh
numbers the moment the panel opens.
"""

from dataclasses import dataclass
from typing import Callable
from PySide6.QtCore import QObject, QTimer

COLLAPSED_INTERVAL_MS = 5 * 60 * 1000
EXPANDED_BASE_INTERVAL_MS = 1000

@dataclass
class ModuleReg:
    name: str
    callback: Callable[[], None]
    cheap: bool = False
    expanded_every: int = 1

class TickDispatcher(QObject):
    def __init__(self, parent=None):
        super().__init__(parent)
        self._modules: list[ModuleReg] = []
        self._expanded_tick_count = 0
        self._is_expanded = False

        self._timer = QTimer(self)
        self._timer.timeout.connect(self._on_tick)
        self._set_collapsed_tier()

    def register(self, name, callback, cheap=False, expanded_every=1):
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
        self.force_full_refresh()
        self._set_expanded_tier()

    def on_collapse(self):
        self._set_collapsed_tier()

    def force_full_refresh(self):
        for mod in self._modules:
            mod.callback()

    def _on_tick(self):
        if not self._is_expanded:
            for mod in self._modules:
                if mod.cheap:
                    mod.callback()
            return
        self._expanded_tick_count += 1
        for mod in self._modules:
            if self._expanded_tick_count % mod.expanded_every == 0:
                mod.callback()

