"""
modules/clipboard/clipboard.py

Clipboard history. Watches the system clipboard and keeps the last
50 copies made anywhere on the machine. Clicking an entry sets the
clipboard back to that text, so it becomes the next thing pasted -
without leaving a duplicate entry at the top (the clicked entry is
just moved back to the front).

State: state/clipboard.json
"""
import uuid
from datetime import datetime, timezone

from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QListWidget, QListWidgetItem,
)
from PySide6.QtGui import QGuiApplication
from PySide6.QtCore import Qt

from core.module import Module
from core.registry import register_module
from core.widgets import ExpandedCard, IconButton

MAX_ENTRIES = 50
COMPACT_PREVIEW_LEN = 40
EXPANDED_PREVIEW_LEN = 90
COMPACT_ROW_LIMIT = 5


def _now_iso():
    return datetime.now(timezone.utc).isoformat()


def _preview(text, limit):
    text = (text or "").strip().replace("\n", " ").replace("\t", " ")
    if not text:
        return "(empty)"
    if len(text) <= limit:
        return text
    return text[:limit].rstrip() + "..."


class ClipboardModule(Module):
    id = "clipboard"
    title = "Clipboard"
    cheap_tick = False
    expanded_every = 1

    def __init__(self, config, state, host=None):
        super().__init__(config, state, host)
        self._card = None
        self._compact_list = None
        self._expanded_list = None
        self._data = self.load_state()
        self._clipboard = None
        # When we write to the clipboard ourselves (re-copy on click),
        # skip the next dataChanged signal so we don't log our own
        # write back into the history.
        self._suppress_next_change = False

    def default_state(self):
        return {"entries": []}

    def _persist(self):
        self.save_state(self._data)

    def build_widget(self):
        self._card = ExpandedCard(self.title.upper())

        hint = QLabel("Click an entry to copy it again")
        hint.setStyleSheet("color: #6b6b74; font-size: 11px;")
        self._card.compact_layout.addWidget(hint)

        self._compact_list = QListWidget()
        self._compact_list.setFixedHeight(140)
        self._compact_list.itemClicked.connect(self._on_item_clicked)
        self._card.compact_layout.addWidget(self._compact_list)

        expanded_hint_row = QHBoxLayout()
        expanded_hint = QLabel("Last 50 copies - click to copy again")
        expanded_hint.setStyleSheet("color: #6b6b74; font-size: 11px;")
        expanded_hint_row.addWidget(expanded_hint)
        expanded_hint_row.addStretch()
        clear_btn = IconButton("\u2715", tooltip="Clear history", variant="danger")
        clear_btn.clicked.connect(self._on_clear)
        expanded_hint_row.addWidget(clear_btn)
        self._card.expanded_layout.addLayout(expanded_hint_row)

        self._expanded_list = QListWidget()
        self._expanded_list.itemClicked.connect(self._on_item_clicked)
        self._card.expanded_layout.addWidget(self._expanded_list, 1)

        self._connect_clipboard()
        self._rebuild()
        return self._card

    def _connect_clipboard(self):
        self._clipboard = QGuiApplication.clipboard()
        self._clipboard.dataChanged.connect(self._on_system_copy)
        # Pick up whatever's already on the clipboard at startup so
        # the very first copy of a session isn't missed.
        current = self._clipboard.text()
        entries = self._data.setdefault("entries", [])
        if current and (not entries or entries[0].get("text") != current):
            entries.insert(0, {
                "id": str(uuid.uuid4()),
                "text": current,
                "created": _now_iso(),
            })
            del entries[MAX_ENTRIES:]
            self._persist()

    def _on_system_copy(self):
        if self._suppress_next_change:
            self._suppress_next_change = False
            return
        text = self._clipboard.text()
        if not text:
            return
        entries = self._data.setdefault("entries", [])
        if entries and entries[0].get("text") == text:
            return
        entries.insert(0, {
            "id": str(uuid.uuid4()),
            "text": text,
            "created": _now_iso(),
        })
        del entries[MAX_ENTRIES:]
        self._persist()
        self._rebuild()

    def _on_item_clicked(self, item):
        entry_id = item.data(Qt.UserRole)
        if not entry_id:
            return
        entries = self._data.get("entries", [])
        entry = next((e for e in entries if e.get("id") == entry_id), None)
        if entry is None:
            return

        text = entry.get("text") or ""
        self._suppress_next_change = True
        self._clipboard.setText(text)

        entries.remove(entry)
        entries.insert(0, entry)
        self._persist()
        self._rebuild()

    def _on_clear(self):
        self._data["entries"] = []
        self._persist()
        self._rebuild()

    def _populate(self, lst, entries, full):
        lst.clear()
        if not entries:
            placeholder = QListWidgetItem("Nothing copied yet")
            placeholder.setFlags(Qt.NoItemFlags)
            lst.addItem(placeholder)
            return
        rows = entries if full else entries[:COMPACT_ROW_LIMIT]
        limit = EXPANDED_PREVIEW_LEN if full else COMPACT_PREVIEW_LEN
        for entry in rows:
            item = QListWidgetItem(_preview(entry.get("text"), limit))
            item.setData(Qt.UserRole, entry.get("id"))
            item.setToolTip(entry.get("text") or "")
            lst.addItem(item)

    def _rebuild(self):
        entries = self._data.get("entries", [])
        if self._compact_list is not None:
            self._populate(self._compact_list, entries, full=False)
        if self._expanded_list is not None:
            self._populate(self._expanded_list, entries, full=True)

    def on_collapse(self):
        self.flush_pending_saves()


register_module("clipboard", ClipboardModule)
