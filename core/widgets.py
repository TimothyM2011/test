"""
core/widgets.py
Small reusable UI building blocks so every module's card looks
consistent (same padding, radius, title style) without repeating
layout code everywhere.
"""

from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QProgressBar, QFrame
)
from PySide6.QtCore import Qt


class Card(QFrame):
    def __init__(self, title: str, parent=None):
        super().__init__(parent)
        self.setProperty("class", "Card")
        self.setObjectName("Card")
        self.setStyleSheet("")  # inherits .Card from global stylesheet
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
    """One label + progress bar row, e.g. 'CPU  ███░░  23%'"""

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

    def set_value(self, percent: float | None, suffix: str = ""):
        if percent is None:
            self.value_label.setText("--")
            self.bar.setValue(0)
            return
        self.bar.setValue(int(percent))
        self.value_label.setText(f"{percent:.0f}%{suffix}")
