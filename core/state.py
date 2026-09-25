"""
core/state.py

Atomic JSON persistence for module state. Files live at
state/<module_id>.json next to config.json. Writes go to a .tmp file
first and are then os.replace'd into place, so a crash mid-write
cannot leave a half-written JSON file.
"""
import json
import os
import threading

from PySide6.QtCore import QObject, QTimer

class StateStore:
    def __init__(self, state_dir: str):
        self._state_dir = state_dir
        self._lock = threading.Lock()
        try:
            os.makedirs(self._state_dir, exist_ok=True)
        except Exception as e:
            print(f"[state] could not create {self._state_dir}: {e}")

    def path_for(self, module_id: str) -> str:
        return os.path.join(self._state_dir, f"{module_id}.json")

    def load(self, module_id: str, default: dict) -> dict:
        path = self.path_for(module_id)
        if not os.path.exists(path):
            return dict(default)
        try:
            with self._lock:
                with open(path, "r", encoding="utf-8") as f:
                    data = json.load(f)
            if not isinstance(data, dict):
                print(f"[state] {module_id}.json root is not an object; using defaults")
                return dict(default)
            merged = dict(default)
            merged.update(data)
            return merged
        except Exception as e:
            print(f"[state] failed to read {path}: {e}; using defaults")
            return dict(default)

    def save(self, module_id: str, data: dict) -> None:
        path = self.path_for(module_id)
        tmp = path + ".tmp"
        try:
            with self._lock:
                with open(tmp, "w", encoding="utf-8") as f:
                    json.dump(data, f, indent=2, ensure_ascii=False)
                os.replace(tmp, path)
        except Exception as e:
            print(f"[state] failed to write {path}: {e}")

class Debouncer(QObject):
    def __init__(self, save_fn, delay_ms: int = 500, parent=None):
        super().__init__(parent)
        self._save_fn = save_fn
        self._pending = None
        self._timer = QTimer(self)
        self._timer.setSingleShot(True)
        self._timer.setInterval(delay_ms)
        self._timer.timeout.connect(self._flush)

    def schedule(self, payload):
        self._pending = payload
        self._timer.start()

    def flush(self):
        if self._timer.isActive():
            self._timer.stop()
        self._flush()

    def _flush(self):
        if self._pending is None:
            return
        payload = self._pending
        self._pending = None
        try:
            self._save_fn(payload)
        except Exception as e:
            print(f"[state] debounced save failed: {e}")
