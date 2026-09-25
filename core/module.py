"""
core/module.py

Base class for sidebar modules.
"""
from PySide6.QtWidgets import QWidget

from core.state import StateStore, Debouncer

class ModuleHost:
    def request_expand(self, module_id: str) -> None:
        pass

    def request_collapse(self, module_id: str) -> None:
        pass

class Module:
    id: str = ""
    title: str = ""
    cheap_tick: bool = False
    expanded_every: int = 1

    def __init__(self, config, state, host=None):
        self.config = config
        self.state_store = state
        self.host = host
        self._widget = None
        self._debouncer = None

    def default_state(self):
        return {}

    def load_state(self):
        return self.state_store.load(self.id, self.default_state())

    def save_state(self, data):
        self.state_store.save(self.id, data)

    def save_state_debounced(self, data, delay_ms=500):
        if self._debouncer is None:
            self._debouncer = Debouncer(
                lambda payload: self.save_state(payload),
                delay_ms=delay_ms,
            )
        self._debouncer.schedule(data)

    def flush_pending_saves(self):
        if self._debouncer is not None:
            self._debouncer.flush()

    def build_widget(self):
        raise NotImplementedError

    def widget(self):
        if self._widget is None:
            self._widget = self.build_widget()
        return self._widget

    def on_expand(self):
        pass

    def on_collapse(self):
        pass

    def on_tick(self):
        pass

    def request_expand(self):
        if self.host is not None:
            self.host.request_expand(self.id)

    def request_collapse(self):
        if self.host is not None:
            self.host.request_collapse(self.id)
