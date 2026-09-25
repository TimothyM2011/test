"""
modules/tasks/tasks.py

Checkbox task list with optional due dates.
"""
import uuid
from datetime import datetime, date

from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QLineEdit, QCheckBox,
    QListWidget, QListWidgetItem, QDateEdit,
)
from PySide6.QtCore import Qt, QDate

from core.module import Module
from core.widgets import ExpandedCard, IconButton
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
        self._data = self.load_state()

    def default_state(self):
        return {"tasks": []}

    def _persist(self):
        self.save_state(self._data)

    def _sorted(self):
        tasks = self._data.get("tasks", [])
        today = _today_local()

        def key(t):
            done = bool(t.get("done"))
            due = _parse_due(t.get("due"))
            overdue = (not done) and due is not None and due < today
            if overdue:
                group = 0
            elif not done and due is not None:
                group = 1
            elif not done:
                group = 2
            else:
                group = 3
            due_sort = due.isoformat() if due else "9999-12-31"
            created = t.get("created") or ""
            return (group, due_sort, created)

        return sorted(tasks, key=key)

    def _is_overdue(self, task):
        if task.get("done"):
            return False
        due = _parse_due(task.get("due"))
        if due is None:
            return False
        return due < _today_local()

    def build_widget(self):
        self._card = ExpandedCard(self.title.upper())

        quick = QHBoxLayout()
        self._quick_add = QLineEdit()
        self._quick_add.setPlaceholderText("Add a task...")
        self._quick_add.returnPressed.connect(self._on_quick_add)
        add_btn = IconButton("+", tooltip="Add")
        add_btn.clicked.connect(self._on_quick_add)
        quick.addWidget(self._quick_add, 1)
        quick.addWidget(add_btn)
        self._card.compact_layout.addLayout(quick)

        self._compact_list = QListWidget()
        self._compact_list.setFixedHeight(140)
        self._card.compact_layout.addWidget(self._compact_list)

        self._expanded_list = QListWidget()
        self._card.expanded_layout.addWidget(self._expanded_list)

        self._rebuild()
        return self._card

    def _make_row(self, task, full):
        row = QWidget()
        layout = QHBoxLayout(row)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(6)

        cb = QCheckBox()
        cb.setChecked(bool(task.get("done")))
        cb.stateChanged.connect(
            lambda _s, tid=task.get("id"): self._on_toggle(tid)
        )
        layout.addWidget(cb)

        label = QLabel(task.get("text") or "")
        if self._is_overdue(task):
            label.setStyleSheet("color: " + DANGER + ";")
        layout.addWidget(label, 1)

        if full:
            due = _parse_due(task.get("due"))
            due_edit = QDateEdit()
            due_edit.setCalendarPopup(True)
            due_edit.setDisplayFormat("yyyy-MM-dd")
            due_edit.setMinimumDate(QDate(2000, 1, 1))
            if due:
                due_edit.setDate(QDate(due.year, due.month, due.day))
            else:
                due_edit.setDate(QDate(2000, 1, 1))
            due_edit.dateChanged.connect(
                lambda qd, tid=task.get("id"): self._on_due_changed(tid, qd)
            )
            layout.addWidget(due_edit)

            del_btn = IconButton("x", tooltip="Delete task")
            del_btn.clicked.connect(
                lambda _=False, tid=task.get("id"): self._on_delete(tid)
            )
            layout.addWidget(del_btn)
        else:
            due = _parse_due(task.get("due"))
            if due is not None:
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

    def _on_quick_add(self):
        text = (self._quick_add.text() or "").strip()
        if not text:
            return
        self._data.setdefault("tasks", []).append({
            "id": str(uuid.uuid4()),
            "text": text,
            "done": False,
            "due": None,
            "created": _now_iso(),
        })
        self._quick_add.clear()
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
        if qdate == QDate(2000, 1, 1):
            new_due = None
        else:
            new_due = f"{qdate.year():04d}-{qdate.month():02d}-{qdate.day():02d}"
        for t in self._data.get("tasks", []):
            if t.get("id") == task_id:
                t["due"] = new_due
                break
        self._persist()
        self._rebuild()