"""
modules/tasks/tasks.py

Checkbox task list with due dates (every task has one - it defaults
to today so there's no ambiguous "unset" date to fight with).
"""
import uuid
from datetime import datetime, date

from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QLineEdit,
    QListWidget, QListWidgetItem, QDateEdit,
)
from PySide6.QtCore import Qt, QDate

from core.module import Module
from core.registry import register_module
from core.widgets import ExpandedCard, IconButton, CheckToggle
from core.theme import DANGER


def _now_iso():
    return datetime.now().isoformat()


def _today_local():
    return datetime.now().date()


def _parse_due(s):
    if not s:
        return None
    try:
        return date.fromisoformat(s)
    except Exception:
        return None


class TasksModule(Module):
    id = "tasks"
    title = "Tasks"
    cheap_tick = False
    expanded_every = 1

    def __init__(self, config, state, host=None):
        super().__init__(config, state, host)
        self._card = None
        self._compact_list = None
        self._expanded_list = None
        self._quick_add = None
        self._quick_add_expanded = None
        self._data = self.load_state()

    def default_state(self):
        return {"tasks": []}

    def _persist(self):
        self.save_state(self._data)

    def _sorted(self):
        """Overdue first, then pending, then done - and within each
        of those groups, the most recently added task on top."""
        tasks = list(self._data.get("tasks", []))
        today = _today_local()

        # Stable sort newest-created-first, then a stable sort by
        # group; the group sort preserves the newest-first order
        # inside each group because Python's sort is stable.
        tasks.sort(key=lambda t: t.get("created") or "", reverse=True)

        def group_key(t):
            done = bool(t.get("done"))
            due = _parse_due(t.get("due"))
            overdue = (not done) and due is not None and due < today
            if overdue:
                return 0
            if not done:
                return 1
            return 2

        tasks.sort(key=group_key)
        return tasks

    def _is_overdue(self, task):
        if task.get("done"):
            return False
        due = _parse_due(task.get("due"))
        if due is None:
            return False
        return due < _today_local()

    def build_widget(self):
        self._card = ExpandedCard(self.title.upper())

        # Compact quick-add.
        quick = QHBoxLayout()
        self._quick_add = QLineEdit()
        self._quick_add.setPlaceholderText("Add a task...")
        self._quick_add.returnPressed.connect(
            lambda: self._add_task_from(self._quick_add))
        add_btn = IconButton("+", tooltip="Add")
        add_btn.clicked.connect(lambda: self._add_task_from(self._quick_add))
        quick.addWidget(self._quick_add, 1)
        quick.addWidget(add_btn)
        self._card.compact_layout.addLayout(quick)

        self._compact_list = QListWidget()
        self._compact_list.setFixedHeight(140)
        self._card.compact_layout.addWidget(self._compact_list)

        # Expanded view gets its OWN quick-add row too - previously
        # this control only lived in the compact layout, which is
        # hidden while the card is expanded, so there was no way to
        # add a task without collapsing first.
        quick_expanded = QHBoxLayout()
        self._quick_add_expanded = QLineEdit()
        self._quick_add_expanded.setPlaceholderText("Add a task...")
        self._quick_add_expanded.returnPressed.connect(
            lambda: self._add_task_from(self._quick_add_expanded))
        add_btn_expanded = IconButton("+", tooltip="Add")
        add_btn_expanded.clicked.connect(
            lambda: self._add_task_from(self._quick_add_expanded))
        quick_expanded.addWidget(self._quick_add_expanded, 1)
        quick_expanded.addWidget(add_btn_expanded)
        self._card.expanded_layout.addLayout(quick_expanded)

        self._expanded_list = QListWidget()
        self._card.expanded_layout.addWidget(self._expanded_list, 1)

        self._rebuild()
        return self._card

    def _make_row(self, task, full):
        row = QWidget()
        layout = QHBoxLayout(row)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(6)

        # Tick-mark toggle instead of a plain blue checkbox.
        cb = CheckToggle(checked=bool(task.get("done")))
        cb.toggled.connect(
            lambda _checked, tid=task.get("id"): self._on_toggle(tid)
        )
        layout.addWidget(cb)

        label = QLabel(task.get("text") or "")
        if self._is_overdue(task):
            label.setStyleSheet("color: " + DANGER + ";")
        layout.addWidget(label, 1)

        due = _parse_due(task.get("due")) or _today_local()

        if full:
            due_edit = QDateEdit()
            due_edit.setCalendarPopup(True)
            due_edit.setDisplayFormat("yyyy-MM-dd")
            due_edit.setDate(QDate(due.year, due.month, due.day))
            due_edit.dateChanged.connect(
                lambda qd, tid=task.get("id"): self._on_due_changed(tid, qd)
            )
            layout.addWidget(due_edit)

            del_btn = IconButton("\u2715", tooltip="Delete task", variant="danger")
            del_btn.clicked.connect(
                lambda _=False, tid=task.get("id"): self._on_delete(tid)
            )
            layout.addWidget(del_btn)
        else:
            meta = QLabel(due.isoformat())
            meta.setStyleSheet("color: #9a9aa2; font-size: 11px;")
            layout.addWidget(meta)

        return row

    def _populate(self, lst, tasks, full):
        lst.clear()
        if not tasks:
            placeholder = QListWidgetItem("No tasks yet" if full else "Nothing pending")
            placeholder.setFlags(Qt.NoItemFlags)
            lst.addItem(placeholder)
            return
        for t in tasks:
            item = QListWidgetItem()
            item.setData(Qt.UserRole, t.get("id"))
            row = self._make_row(t, full)
            item.setSizeHint(row.sizeHint())
            lst.addItem(item)
            lst.setItemWidget(item, row)

    def _rebuild(self):
        tasks = self._sorted()
        if self._compact_list is not None:
            self._populate(self._compact_list, tasks[:5], full=False)
        if self._expanded_list is not None:
            self._populate(self._expanded_list, tasks, full=True)

    def _add_task_from(self, line_edit):
        text = (line_edit.text() or "").strip()
        if not text:
            return
        self._data.setdefault("tasks", []).append({
            "id": str(uuid.uuid4()),
            "text": text,
            "done": False,
            # Every task carries a real, known date from the moment
            # it's created rather than an unset/sentinel value - new
            # tasks default to today's due date, editable afterward.
            "due": _today_local().isoformat(),
            "created": _now_iso(),
        })
        line_edit.clear()
        self._persist()
        self._rebuild()

    def _on_toggle(self, task_id):
        for t in self._data.get("tasks", []):
            if t.get("id") == task_id:
                t["done"] = not bool(t.get("done"))
                break
        self._persist()
        self._rebuild()

    def _on_delete(self, task_id):
        self._data["tasks"] = [t for t in self._data.get("tasks", [])
                               if t.get("id") != task_id]
        self._persist()
        self._rebuild()

    def _on_due_changed(self, task_id, qdate):
        new_due = f"{qdate.year():04d}-{qdate.month():02d}-{qdate.day():02d}"
        for t in self._data.get("tasks", []):
            if t.get("id") == task_id:
                t["due"] = new_due
                break
        self._persist()
        self._rebuild()

register_module("tasks", TasksModule)
