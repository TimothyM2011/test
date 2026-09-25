"""
modules/notes/notes.py

Named notes with a list and editor. Compact view shows recent titles,
expanded view shows the full list plus a text editor.

State: state/notes.json
"""
import uuid
from datetime import datetime, timezone

from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QLineEdit,
    QPlainTextEdit, QListWidget, QListWidgetItem, QSplitter,
    QMessageBox,
)
from PySide6.QtCore import Qt

from core.module import Module
from core.widgets import ExpandedCard, IconButton

def _now_iso():
    return datetime.now(timezone.utc).isoformat()

class NotesModule(Module):
    id = "notes"
    title = "Notes"
    cheap_tick = False
    expanded_every = 1

    def __init__(self, config, state, host=None):
        super().__init__(config, state, host)
        self._card = None
        self._compact_list = None
        self._expanded_list = None
        self._title_edit = None
        self._body_edit = None
        self._data = self.load_state()
        self._suppress = False

    def default_state(self):
        return {"notes": [], "selected_id": None}

    def _persist(self):
        self.save_state(self._data)

    def _persist_debounced(self):
        self.save_state_debounced(self._data, delay_ms=500)

    def _find(self, note_id):
        for n in self._data.get("notes", []):
            if n.get("id") == note_id:
                return n
        return None

    def _sorted(self):
        return sorted(
            self._data.get("notes", []),
            key=lambda n: n.get("updated") or "",
            reverse=True,
        )

    def build_widget(self):
        self._card = ExpandedCard(self.title.upper())

        top = QHBoxLayout()
        top.addWidget(QLabel("Recent"))
        top.addStretch()
        add1 = IconButton("+", tooltip="New note")
        add1.clicked.connect(self._on_add)
        top.addWidget(add1)
        self._card.compact_layout.addLayout(top)

        self._compact_list = QListWidget()
        self._compact_list.setFixedHeight(120)
        self._compact_list.itemClicked.connect(self._on_compact_click)
        self._card.compact_layout.addWidget(self._compact_list)

        self._expanded_list = QListWidget()
        self._expanded_list.itemClicked.connect(self._on_expanded_click)

        left = QWidget()
        ll = QVBoxLayout(left)
        ll.setContentsMargins(0, 0, 0, 0)
        lh = QHBoxLayout()
        lh.addWidget(QLabel("All notes"))
        lh.addStretch()
        add2 = IconButton("+", tooltip="New note")
        add2.clicked.connect(self._on_add)
        lh.addWidget(add2)
        ll.addLayout(lh)
        ll.addWidget(self._expanded_list)

        right = QWidget()
        rl = QVBoxLayout(right)
        rl.setContentsMargins(0, 0, 0, 0)

        title_row = QHBoxLayout()
        self._title_edit = QLineEdit()
        self._title_edit.setPlaceholderText("Title")
        self._title_edit.textEdited.connect(self._on_title_edit)
        del_btn = IconButton("x", tooltip="Delete note")
        del_btn.clicked.connect(self._on_delete)
        title_row.addWidget(self._title_edit, 1)
        title_row.addWidget(del_btn)
        rl.addLayout(title_row)

        self._body_edit = QPlainTextEdit()
        self._body_edit.setPlaceholderText("Write here...")
        self._body_edit.textChanged.connect(self._on_body_edit)
        rl.addWidget(self._body_edit, 1)

        split = QSplitter(Qt.Horizontal)
        split.addWidget(left)
        split.addWidget(right)
        split.setStretchFactor(0, 1)
        split.setStretchFactor(1, 2)
        split.setSizes([160, 320])
        self._card.expanded_layout.addWidget(split)

        self._rebuild()
        return self._card

    def _display_title(self, note):
        t = (note.get("title") or "").strip()
        return t if t else "Untitled"

    def _rebuild(self):
        notes = self._sorted()
        selected = self._data.get("selected_id")

        if self._compact_list is not None:
            self._compact_list.clear()
            for n in notes[:8]:
                item = QListWidgetItem(self._display_title(n))
                item.setData(Qt.UserRole, n.get("id"))
                self._compact_list.addItem(item)

        if self._expanded_list is not None:
            self._expanded_list.clear()
            for n in notes:
                item = QListWidgetItem(self._display_title(n))
                item.setData(Qt.UserRole, n.get("id"))
                if n.get("id") == selected:
                    item.setSelected(True)
                self._expanded_list.addItem(item)

        self._load_editor(selected)

    def _load_editor(self, note_id):
        if self._title_edit is None or self._body_edit is None:
            return
        self._suppress = True
        note = self._find(note_id) if note_id else None
        if note is None:
            self._title_edit.setText("")
            self._body_edit.setPlainText("")
            self._title_edit.setEnabled(False)
            self._body_edit.setEnabled(False)
        else:
            self._title_edit.setEnabled(True)
            self._body_edit.setEnabled(True)
            self._title_edit.setText(note.get("title") or "")
            self._body_edit.setPlainText(note.get("body") or "")
        self._suppress = False

    def _on_add(self):
        note = {
            "id": str(uuid.uuid4()),
            "title": "",
            "body": "",
            "updated": _now_iso(),
        }
        self._data.setdefault("notes", []).append(note)
        self._data["selected_id"] = note["id"]
        self._persist()
        self._rebuild()

    def _on_delete(self):
        note_id = self._data.get("selected_id")
        if not note_id:
            return
        box = QMessageBox(self._card)
        box.setWindowTitle("Delete note")
        box.setText("Delete this note?")
        box.setStandardButtons(QMessageBox.Yes | QMessageBox.No)
        box.setDefaultButton(QMessageBox.No)
        if box.exec() != QMessageBox.Yes:
            return
        self._data["notes"] = [n for n in self._data.get("notes", [])
                               if n.get("id") != note_id]
        self._data["selected_id"] = None
        self._persist()
        self._rebuild()

    def _select(self, note_id):
        self._data["selected_id"] = note_id
        self._persist()
        self._rebuild()
        if not self._card.is_expanded():
            self.request_expand()

    def _on_compact_click(self, item):
        self._select(item.data(Qt.UserRole))

    def _on_expanded_click(self, item):
        self._select(item.data(Qt.UserRole))

    def _on_title_edit(self, text):
        if self._suppress:
            return
        note = self._find(self._data.get("selected_id"))
        if note is None:
            return
        note["title"] = text
        note["updated"] = _now_iso()
        self._persist_debounced()

    def _on_body_edit(self):
        if self._suppress:
            return
        note = self._find(self._data.get("selected_id"))
        if note is None:
            return
        note["body"] = self._body_edit.toPlainText()
        note["updated"] = _now_iso()
        self._persist_debounced()

    def on_collapse(self):
        self.flush_pending_saves()
