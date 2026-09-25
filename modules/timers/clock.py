"""
modules/timers/clock.py

One module, two modes: Timer and Stopwatch.

Timers persist across restarts by storing started_at (UTC ISO) and
elapsed_ms. On load, if running is true, elapsed is computed from
wall-clock so time spent with the app closed counts.

State: state/clock.json
"""
import uuid
from datetime import datetime, timezone

from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QLineEdit, QListWidget,
    QListWidgetItem, QPushButton, QSpinBox, QStackedWidget,
)
from PySide6.QtCore import Qt

from core.module import Module
from core.widgets import ExpandedCard, IconButton


def _now_iso():
    return datetime.now(timezone.utc).isoformat()


def _parse_iso(s):
    if not s:
        return None
    try:
        dt = datetime.fromisoformat(s)
        if dt.tzinfo is None:
            dt = dt.replace(tzinfo=timezone.utc)
        return dt
    except Exception:
        return None


def _fmt_ms(ms):
    if ms < 0:
        ms = 0
    total_s = ms // 1000
    h = total_s // 3600
    m = (total_s % 3600) // 60
    s = total_s % 60
    if h > 0:
        return f"{h}:{m:02d}:{s:02d}"
    return f"{m:02d}:{s:02d}"


class ClockModule(Module):
    id = "clock"
    title = "Clock"
    cheap_tick = False
    expanded_every = 1

    def __init__(self, config, state, host=None):
        super().__init__(config, state, host)
        self._card = None
        self._mode_stack = None
        self._compact_time = None
        self._timer_list = None
        self._stopwatch_label = None
        self._timer_toggle = None
        self._sw_toggle = None
        self._name_edit = None
        self._mins_spin = None
        self._data = self.load_state()
        self._normalize_after_load()

    def default_state(self):
        return {
            "mode": "timer",
            "timers": [],
            "stopwatch": {"elapsed_ms": 0, "running": False, "started_at": None},
        }

    def _persist(self):
        self.save_state(self._data)

    def _normalize_after_load(self):
        now = datetime.now(timezone.utc)
        for t in self._data.get("timers", []):
            if t.get("running"):
                started = _parse_iso(t.get("started_at"))
                if started is None:
                    t["running"] = False
                    t["started_at"] = None
                    continue
                delta_ms = int((now - started).total_seconds() * 1000)
                t["elapsed_ms"] = int(t.get("elapsed_ms") or 0) + max(0, delta_ms)
                duration = int(t.get("duration_ms") or 0)
                if duration and t["elapsed_ms"] >= duration:
                    t["elapsed_ms"] = duration
                    t["running"] = False
                    t["started_at"] = None
                else:
                    t["started_at"] = now.isoformat()

        sw = self._data.setdefault("stopwatch",
                                   {"elapsed_ms": 0, "running": False, "started_at": None})
        if sw.get("running"):
            started = _parse_iso(sw.get("started_at"))
            if started is None:
                sw["running"] = False
                sw["started_at"] = None
            else:
                delta_ms = int((now - started).total_seconds() * 1000)
                sw["elapsed_ms"] = int(sw.get("elapsed_ms") or 0) + max(0, delta_ms)
                sw["started_at"] = now.isoformat()

        self._persist()

    def _remaining_ms(self, timer):
        duration = int(timer.get("duration_ms") or 0)
        elapsed = int(timer.get("elapsed_ms") or 0)
        if timer.get("running"):
            started = _parse_iso(timer.get("started_at"))
            if started is not None:
                now = datetime.now(timezone.utc)
                elapsed += int((now - started).total_seconds() * 1000)
        if duration <= 0:
            return 0
        return max(0, duration - elapsed)

    def _stopwatch_ms(self):
        sw = self._data.get("stopwatch", {})
        elapsed = int(sw.get("elapsed_ms") or 0)
        if sw.get("running"):
            started = _parse_iso(sw.get("started_at"))
            if started is not None:
                now = datetime.now(timezone.utc)
                elapsed += int((now - started).total_seconds() * 1000)
        return max(0, elapsed)

    def build_widget(self):
        self._card = ExpandedCard(self.title.upper())

        toggle_row = QHBoxLayout()
        self._timer_toggle = QPushButton("Timer")
        self._sw_toggle = QPushButton("Stopwatch")
        self._timer_toggle.setCheckable(True)
        self._sw_toggle.setCheckable(True)
        self._timer_toggle.clicked.connect(lambda: self._set_mode("timer"))
        self._sw_toggle.clicked.connect(lambda: self._set_mode("stopwatch"))
        toggle_row.addWidget(self._timer_toggle)
        toggle_row.addWidget(self._sw_toggle)
        toggle_row.addStretch()
        self._card.compact_layout.addLayout(toggle_row)

        self._compact_time = QLabel("--:--")
        self._compact_time.setStyleSheet(
            "font-size: 22px; font-weight: 600; letter-spacing: 2px;"
        )
        self._card.compact_layout.addWidget(self._compact_time)

        self._mode_stack = QStackedWidget()

        timer_page = QWidget()
        tp = QVBoxLayout(timer_page)
        tp.setContentsMargins(0, 0, 0, 0)
        tp.setSpacing(6)

        add_row = QHBoxLayout()
        self._name_edit = QLineEdit()
        self._name_edit.setPlaceholderText("Timer name")
        self._mins_spin = QSpinBox()
        self._mins_spin.setRange(1, 999)
        self._mins_spin.setValue(25)
        self._mins_spin.setSuffix(" min")
        add_btn = IconButton("+", tooltip="Add timer")
        add_btn.clicked.connect(self._on_add_timer)
        add_row.addWidget(self._name_edit, 1)
        add_row.addWidget(self._mins_spin)
        add_row.addWidget(add_btn)
        tp.addLayout(add_row)

        self._timer_list = QListWidget()
        tp.addWidget(self._timer_list, 1)
        self._mode_stack.addWidget(timer_page)

        sw_page = QWidget()
        sl = QVBoxLayout(sw_page)
        sl.setContentsMargins(0, 0, 0, 0)
        sl.setSpacing(6)

        self._stopwatch_label = QLabel("00:00")
        self._stopwatch_label.setAlignment(Qt.AlignCenter)
        self._stopwatch_label.setStyleSheet(
            "font-size: 34px; font-weight: 600; letter-spacing: 3px;"
        )
        sl.addWidget(self._stopwatch_label)

        sw_controls = QHBoxLayout()
        sw_start = QPushButton("Start")
        sw_start.clicked.connect(self._on_sw_start)
        sw_pause = QPushButton("Pause")
        sw_pause.clicked.connect(self._on_sw_pause)
        sw_reset = QPushButton("Reset")
        sw_reset.clicked.connect(self._on_sw_reset)
        sw_controls.addWidget(sw_start)
        sw_controls.addWidget(sw_pause)
        sw_controls.addWidget(sw_reset)
        sl.addLayout(sw_controls)
        sl.addStretch()
        self._mode_stack.addWidget(sw_page)

        self._card.expanded_layout.addWidget(self._mode_stack, 1)

        self._apply_mode()
        self._rebuild_timers()
        self.on_tick()
        return self._card

    def _set_mode(self, mode):
        self._data["mode"] = mode
        self._persist()
        self._apply_mode()

    def _apply_mode(self):
        mode = self._data.get("mode", "timer")
        is_timer = mode == "timer"
        if self._timer_toggle is not None:
            self._timer_toggle.setChecked(is_timer)
            self._sw_toggle.setChecked(not is_timer)
        if self._mode_stack is not None:
            self._mode_stack.setCurrentIndex(0 if is_timer else 1)

    def _rebuild_timers(self):
        if self._timer_list is None:
            return
        self._timer_list.clear()
        timers = self._data.get("timers", [])
        if not timers:
            item = QListWidgetItem("No timers yet")
            item.setFlags(Qt.NoItemFlags)
            self._timer_list.addItem(item)
            return
        for t in timers:
            item = QListWidgetItem()
            item.setData(Qt.UserRole, t.get("id"))
            row = self._make_timer_row(t)
            item.setSizeHint(row.sizeHint())
            self._timer_list.addItem(item)
            self._timer_list.setItemWidget(item, row)

    def _make_timer_row(self, timer):
        row = QWidget()
        layout = QHBoxLayout(row)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(6)

        name = QLabel(timer.get("name") or "Timer")
        name.setFixedWidth(70)
        layout.addWidget(name)

        remaining = QLabel(_fmt_ms(self._remaining_ms(timer)))
        remaining.setStyleSheet(
            "font-size: 16px; font-weight: 600; letter-spacing: 1px;"
        )
        remaining.setMinimumWidth(70)
        layout.addWidget(remaining, 1)

        toggle_text = "Pause" if timer.get("running") else "Start"
        toggle = QPushButton(toggle_text)
        toggle.setFixedWidth(60)
        toggle.clicked.connect(
            lambda _=False, tid=timer.get("id"): self._on_timer_toggle(tid)
        )
        layout.addWidget(toggle)

        reset = QPushButton("Reset")
        reset.setFixedWidth(60)
        reset.clicked.connect(
            lambda _=False, tid=timer.get("id"): self._on_timer_reset(tid)
        )
        layout.addWidget(reset)

        del_btn = IconButton("x", tooltip="Delete timer")
        del_btn.clicked.connect(
            lambda _=False, tid=timer.get("id"): self._on_timer_delete(tid)
        )
        layout.addWidget(del_btn)

        return row

    def _on_add_timer(self):
        name = (self._name_edit.text() or "").strip() or "Timer"
        duration_ms = self._mins_spin.value() * 60 * 1000
        self._data.setdefault("timers", []).append({
            "id": str(uuid.uuid4()),
            "name": name,
            "duration_ms": duration_ms,
            "elapsed_ms": 0,
            "running": False,
            "started_at": None,
        })
        self._name_edit.clear()
        self._persist()
        self._rebuild_timers()
        self.on_tick()

    def _find_timer(self, timer_id):
        for t in self._data.get("timers", []):
            if t.get("id") == timer_id:
                return t
        return None

    def _on_timer_toggle(self, timer_id):
        t = self._find_timer(timer_id)
        if t is None:
            return
        now = datetime.now(timezone.utc)
        if t.get("running"):
            started = _parse_iso(t.get("started_at"))
            if started is not None:
                delta = int((now - started).total_seconds() * 1000)
                t["elapsed_ms"] = int(t.get("elapsed_ms") or 0) + max(0, delta)
            t["running"] = False
            t["started_at"] = None
        else:
            duration = int(t.get("duration_ms") or 0)
            if duration and int(t.get("elapsed_ms") or 0) >= duration:
                t["elapsed_ms"] = 0
            t["running"] = True
            t["started_at"] = now.isoformat()
        self._persist()
        self._rebuild_timers()
        self.on_tick()

    def _on_timer_reset(self, timer_id):
        t = self._find_timer(timer_id)
        if t is None:
            return
        t["elapsed_ms"] = 0
        t["running"] = False
        t["started_at"] = None
        self._persist()
        self._rebuild_timers()
        self.on_tick()

    def _on_timer_delete(self, timer_id):
        self._data["timers"] = [t for t in self._data.get("timers", [])
                                if t.get("id") != timer_id]
        self._persist()
        self._rebuild_timers()
        self.on_tick()

    def _on_sw_start(self):
        sw = self._data.setdefault("stopwatch",
                                   {"elapsed_ms": 0, "running": False, "started_at": None})
        if sw.get("running"):
            return
        sw["running"] = True
        sw["started_at"] = datetime.now(timezone.utc).isoformat()
        self._persist()
        self.on_tick()

    def _on_sw_pause(self):
        sw = self._data.setdefault("stopwatch",
                                   {"elapsed_ms": 0, "running": False, "started_at": None})
        if not sw.get("running"):
            return
        started = _parse_iso(sw.get("started_at"))
        if started is not None:
            now = datetime.now(timezone.utc)
            delta = int((now - started).total_seconds() * 1000)
            sw["elapsed_ms"] = int(sw.get("elapsed_ms") or 0) + max(0, delta)
        sw["running"] = False
        sw["started_at"] = None
        self._persist()
        self.on_tick()

    def _on_sw_reset(self):
        self._data["stopwatch"] = {"elapsed_ms": 0, "running": False, "started_at": None}
        self._persist()
        self.on_tick()

    def on_tick(self):
        mode = self._data.get("mode", "timer")

        if mode == "timer" and self._compact_time is not None:
            timers = self._data.get("timers", [])
            if timers:
                self._compact_time.setText(_fmt_ms(self._remaining_ms(timers[0])))
            else:
                self._compact_time.setText("--:--")

        if mode == "stopwatch" and self._compact_time is not None:
            self._compact_time.setText(_fmt_ms(self._stopwatch_ms()))

        if self._stopwatch_label is not None:
            self._stopwatch_label.setText(_fmt_ms(self._stopwatch_ms()))

        if mode == "timer" and self._timer_list is not None:
            for i in range(self._timer_list.count()):
                item = self._timer_list.item(i)
                tid = item.data(Qt.UserRole)
                if not tid:
                    continue
                row = self._timer_list.itemWidget(item)
                if row is None:
                    continue
                t = self._find_timer(tid)
                if t is None:
                    continue
                labels = row.findChildren(QLabel)
                if len(labels) >= 2:
                    labels[1].setText(_fmt_ms(self._remaining_ms(t)))
                if t.get("running") and self._remaining_ms(t) == 0:
                    t["elapsed_ms"] = int(t.get("duration_ms") or 0)
                    t["running"] = False
                    t["started_at"] = None
                    self._persist()
                    self._rebuild_timers()

    def on_collapse(self):
        self.flush_pending_saves()