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

from core.theme import DANGER, ACCENT

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
    """
    Small square button for header/row affordances (chevrons, +, delete).

    variant="default": neutral, lights up on hover (add, expand, etc).
    variant="danger": stays neutral at rest, turns red on hover/press
      so destructive actions (delete, clear) are visually distinct
      before the click, not just via tooltip text.

    Deliberately larger than a bare text glyph (28px, up from 22px)
    and always paired with a tooltip so the affordance reads as a
    button, not stray punctuation.
    """

    def __init__(self, text: str, parent=None, size: int = 28, tooltip: str = "",
                 variant: str = "default"):
        super().__init__(text, parent)
        self.setFixedSize(size, size)
        self.setCursor(Qt.PointingHandCursor)

        if variant == "danger":
            hover_color = DANGER
            hover_bg = "#3a2323"
            pressed_bg = "#2c1a1a"
        else:
            hover_color = "#e6e6e8"
            hover_bg = "#2a2a30"
            pressed_bg = "#1c1c20"

        self.setStyleSheet(
            "QPushButton {"
            "  background: transparent;"
            "  border: 1px solid transparent;"
            "  color: #9a9aa2;"
            "  font-size: 14px;"
            "  font-weight: 600;"
            "  padding: 0;"
            "}"
            "QPushButton:hover {"
            f"  color: {hover_color};"
            f"  background-color: {hover_bg};"
            "  border-radius: 5px;"
            "}"
            "QPushButton:pressed {"
            f"  background-color: {pressed_bg};"
            "  border-radius: 5px;"
            "}"
        )
        if tooltip:
            self.setToolTip(tooltip)
            self.setAccessibleName(tooltip)

class CheckToggle(QPushButton):
    """
    A checkable square control that shows a check mark (not a filled
    blue box) when checked, with a border that's actually visible at
    rest so it reads as a checkbox before you've ever clicked it.
    """

    def __init__(self, checked: bool = False, parent=None, size: int = 20):
        super().__init__(parent)
        self.setCheckable(True)
        self.setChecked(checked)
        self.setFixedSize(size, size)
        self.setCursor(Qt.PointingHandCursor)
        self.setText("\u2713" if checked else "")
        self.toggled.connect(self._on_toggled)
        self._apply_style()

    def _on_toggled(self, checked: bool):
        self.setText("\u2713" if checked else "")
        self._apply_style()

    def _apply_style(self):
        self.setStyleSheet(
            "QPushButton {"
            "  border-radius: 4px;"
            "  border: 1px solid #6b6b74;"
            "  background-color: #16161a;"
            "  color: #101014;"
            "  font-size: 12px;"
            "  font-weight: 700;"
            "  padding: 0;"
            "}"
            "QPushButton:checked {"
            f"  background-color: {ACCENT};"
            f"  border-color: {ACCENT};"
            "  color: #101014;"
            "}"
            "QPushButton:hover {"
            f"  border-color: {ACCENT};"
            "}"
        )


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

        self.expand_btn = IconButton("\u2304", tooltip="Expand")
        self._expand_btn_base_style = self.expand_btn.styleSheet()

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
            self.expand_btn.setText("\u2303")
            self.expand_btn.setToolTip("Collapse")
            self.expand_btn.setStyleSheet(
                self._expand_btn_base_style + f"QPushButton {{ color: {ACCENT}; }}"
            )
            # The default card border (#33333a on a #232328 background)
            # is nearly invisible. Give the expanded card a clearly
            # visible outline so its bounds actually read as a box
            # rather than blending into the sidebar.
            self.setStyleSheet(
                f"QFrame#Card {{ border: 1px solid {ACCENT}; border-radius: 10px; }}"
            )
        else:
            self.expanded_widget.hide()
            self.compact_widget.show()
            self.expand_btn.setText("\u2304")
            self.expand_btn.setToolTip("Expand")
            self.expand_btn.setStyleSheet(self._expand_btn_base_style)
            self.setStyleSheet("")

    def is_expanded(self) -> bool:
        return self._expanded

    def _on_expand_clicked(self):
        if self._expanded:
            self.collapse_requested.emit()
        else:
            self.expand_requested.emit()
