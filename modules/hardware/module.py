"""
modules/hardware/module.py

Wraps the existing hardware data functions as a sidebar Module.
Behavior is unchanged: three MetricRows labelled CPU / RAM / GPU,
refreshed once per second while open.
"""
from PySide6.QtWidgets import QWidget

from core.module import Module
from core.widgets import Card, MetricRow
from modules.hardware import hardware

class HardwareModule(Module):
    id = "hardware"
    title = "System"
    cheap_tick = True
    expanded_every = 1

    def __init__(self, config, state, host=None):
        super().__init__(config, state, host)
        self._card = None
        self._cpu_row = None
        self._ram_row = None
        self._gpu_row = None
        self._last_stats = {}

    def build_widget(self) -> QWidget:
        self._card = Card(self.title.upper())
        self._cpu_row = MetricRow("CPU")
        self._ram_row = MetricRow("RAM")
        self._gpu_row = MetricRow("GPU")
        self._card.body.addWidget(self._cpu_row)
        self._card.body.addWidget(self._ram_row)
        self._card.body.addWidget(self._gpu_row)
        self.on_tick()
        return self._card

    def on_tick(self):
        if self._card is None:
            return
        try:
            stats = hardware.read_full_stats()
        except Exception as e:
            print(f"[hardware] read failed: {e}")
            return
        self._last_stats = stats
        if self._cpu_row is not None:
            self._cpu_row.set_value(stats.get("cpu_percent"))
        if self._ram_row is not None:
            self._ram_row.set_value(stats.get("ram_percent"))
        if self._gpu_row is not None:
            self._gpu_row.set_value(stats.get("gpu_percent"))
