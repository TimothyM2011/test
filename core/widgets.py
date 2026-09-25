"""
core/widgets.py

Reusable UI building blocks.

Card and MetricRow are unchanged from the previous build so the hardware
card keeps working. ExpandedCard adds a compact/expanded swap with a
chevron affordance for the new modules.
"""
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QProgressBar, QFrame,
    QPushButton,
)
from PySide6.QtCore import Qt, Signal

class Card(QFrame):
    def __init__(self, title: str, parent=None):
        super().__init__(parent)
        self.setProperty("class", "Card")
        self.setObjectName("Card")
        outer = QVBoxLayout(self)
        outer.setContentsMargins(14, 12, 14, 12)
        outer.setSpacing(8)

        title_label = QLabel(title.upper())
        title_label.setProperty("class", "CardTitle")
        outer.addWidget(title_label)

        self.body = QVBoxLayout()
        self.body.setSpacing(6)
        outer.addLayout(self.body)

class MetricRow(QWidget):
    """One label + progress bar row, e.g. 'CPU  xxx  23%'"""

    def __init__(self, label: str, parent=None):
        super().__init__(parent)
        layout = QHBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(8)

        self.label = QLabel(label)
        self.label.setFixedWidth(36)
        self.label.setStyleSheet("color: #9a9aa2; font-size: 11px;")

        self.bar = QProgressBar()
        self.bar.setRange(0, 100)
        self.bar.setTextVisible(False)
        self.bar.setFixedHeight(6)

        self.value_label = QLabel("--")
        self.value_label.setFixedWidth(64)
        self.value_label.setAlignment(Qt.AlignRight)
        self.value_label.setStyleSheet("color: #e6e6e8; font-size: 11px;")

        layout.addWidget(self.label)
        layout.addWidget(self.bar, 1)
        layout.addWidget(self.value_label)

    def set_value(self, percent, suffix: str = ""):
        if percent is None:
            self.value_label.setText("--")
            self.bar.setValue(0)
            return
        self.bar.setValue(int(percent))
        self.value_label.setText(f"{percent:.0f}%{suffix}")

class IconButton(QPushButton):
    """Small square button for header affordances (chevrons, +, x)."""

    def __init__(self, text: str, parent=None, size: int = 22, tooltip: str = ""):
        super().__init__(text, parent)
        self.setFixedSize(size, size)
        self.setCursor(Qt.PointingHandCursor)
        self.setStyleSheet(
            "QPushButton {"
            "  background: transparent;"
            "  border: none;"
            "  color: #9a9aa2;"
            "  font-size: 13px;"
            "  padding: 0;"
            "}"
            "QPushButton:hover {"
            "  color: #e6e6e8;"
            "  background-color: #2a2a30;"
            "  border-radius: 4px;"
            "}"
        )
        if tooltip:
            self.setToolTip(tooltip)

class ExpandedCard(QFrame):
    """
    A Card that swaps between a compact widget and an expanded widget.

    The card does NOT resize the sidebar by itself - it emits
    expand_requested/collapse_requested and lets the Sidebar decide.
    """

    expand_requested = Signal()
    collapse_requested = Signal()

    def __init__(self, title: str, parent=None):
        super().__init__(parent)
        self.setProperty("class", "Card")
        self.setObjectName("Card")
        self._expanded = False

        outer = QVBoxLayout(self)
        outer.setContentsMargins(14, 12, 14, 12)
        outer.setSpacing(8)

        header = QHBoxLayout()
        header.setSpacing(6)

        self.title_label = QLabel(title.upper())
        self.title_label.setProperty("class", "CardTitle")

        self.expand_btn = IconButton(">", tooltip="Expand")

        header.addWidget(self.title_label)
        header.addStretch()
        header.addWidget(self.expand_btn)
        outer.addLayout(header)

        self.compact_widget = QWidget()
        self.compact_layout = QVBoxLayout(self.compact_widget)
        self.compact_layout.setContentsMargins(0, 0, 0, 0)
        self.compact_layout.setSpacing(6)
        outer.addWidget(self.compact_widget)

        self.expanded_widget = QWidget()
        self.expanded_layout = QVBoxLayout(self.expanded_widget)
        self.expanded_layout.setContentsMargins(0, 0, 0, 0)
        self.expanded_layout.setSpacing(6)
        self.expanded_widget.hide()
        outer.addWidget(self.expanded_widget)

        self.expand_btn.clicked.connect(self._on_expand_clicked)

    def set_expanded(self, expanded: bool) -> None:
        if expanded == self._expanded:
            return
        self._expanded = expanded
        if expanded:
            self.compact_widget.hide()
            self.expanded_widget.show()
            self.expand_btn.setText("<")
            self.expand_btn.setToolTip("Collapse")
        else:
            self.expanded_widget.hide()
            self.compact_widget.show()
            self.expand_btn.setText(">")
            self.expand_btn.setToolTip("Expand")

    def is_expanded(self) -> bool:
        return self._expanded

    def _on_expand_clicked(self):
        if self._expanded:
            self.collapse_requested.emit()
        else:
            self.expand_requested.emit()
