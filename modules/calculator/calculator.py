"""
modules/calculator/calculator.py

Basic four-function calculator. No eval() on any input - button
presses drive a small accumulator state machine, so there's nothing
resembling an expression parser or code execution involved.

Compact view: a read-only display, so you can glance at whatever you
last worked out without expanding.
Expanded view: full keypad.
"""
from PySide6.QtWidgets import (
    QWidget, QGridLayout, QLineEdit, QPushButton, QSizePolicy,
)
from PySide6.QtCore import Qt

from core.module import Module
from core.registry import register_module
from core.theme import ACCENT, BORDER
from core.widgets import ExpandedCard

MAX_DISPLAY_CHARS = 16


def _format_number(value: float) -> str:
    if value == int(value) and abs(value) < 1e15:
        text = str(int(value))
    else:
        text = f"{value:.10g}"
    if len(text) > MAX_DISPLAY_CHARS:
        text = f"{value:.6g}"
    return text


class CalcButton(QPushButton):
    """Keypad button. variant picks the color treatment:
    'num' (neutral), 'op' (accent, for + - x / =), 'func' (muted, for
    C / +- / %)."""

    def __init__(self, text, variant="num", parent=None):
        super().__init__(text, parent)
        self.setCursor(Qt.PointingHandCursor)
        self.setMinimumHeight(36)
        self.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)

        if variant == "op":
            bg, bg_hover, fg = ACCENT, "#8adfff", "#101014"
        elif variant == "func":
            bg, bg_hover, fg = "#2a2a30", "#33333c", "#e6e6e8"
        else:
            bg, bg_hover, fg = "#232328", "#2c2c33", "#e6e6e8"

        self.setStyleSheet(
            "QPushButton {"
            f"  background-color: {bg};"
            f"  color: {fg};"
            f"  border: 1px solid {BORDER};"
            "  border-radius: 8px;"
            "  font-size: 15px;"
            "  font-weight: 600;"
            "}"
            "QPushButton:hover {"
            f"  background-color: {bg_hover};"
            "}"
            "QPushButton:pressed {"
            "  background-color: #16161a;"
            "}"
        )


class CalculatorModule(Module):
    id = "calculator"
    title = "Calculator"
    cheap_tick = False
    expanded_every = 1

    def __init__(self, config, state, host=None):
        super().__init__(config, state, host)
        self._compact_display = None
        self._expanded_display = None

        # Runtime accumulator state - deliberately not persisted;
        # a calculator's mid-calculation state isn't meaningful to
        # restore after a restart, only the last shown result is.
        self._display = "0"
        self._stored_value = None
        self._pending_op = None
        self._fresh_entry = True

        self._data = self.load_state()
        self._display = self._data.get("last_display", "0")

    def default_state(self):
        return {"last_display": "0"}

    def _persist(self):
        self._data["last_display"] = self._display
        self.save_state(self._data)

    def build_widget(self):
        return self._build_full_card()

    def _make_display(self):
        display = QLineEdit()
        display.setReadOnly(True)
        display.setAlignment(Qt.AlignRight)
        display.setText(self._display)
        display.setStyleSheet(
            "QLineEdit {"
            "  font-size: 24px;"
            "  font-weight: 600;"
            "  padding: 10px 12px;"
            "  background-color: #101014;"
            f"  border: 1px solid {BORDER};"
            "  border-radius: 8px;"
            "}"
        )
        return display

    def _build_full_card(self):
        self._card = ExpandedCard(self.title.upper())

        self._compact_display = self._make_display()
        self._card.compact_layout.addWidget(self._compact_display)

        self._expanded_display = self._make_display()
        self._card.expanded_layout.addWidget(self._expanded_display)

        grid = QGridLayout()
        grid.setSpacing(6)
        for col in range(4):
            grid.setColumnStretch(col, 1)

        rows = [
            [("C", "func", self._on_clear), ("+/-", "func", self._on_sign),
             ("%", "func", self._on_percent), ("/", "op", lambda: self._on_op("/"))],
            [("7", "num", lambda: self._on_digit("7")), ("8", "num", lambda: self._on_digit("8")),
             ("9", "num", lambda: self._on_digit("9")), ("*", "op", lambda: self._on_op("*"))],
            [("4", "num", lambda: self._on_digit("4")), ("5", "num", lambda: self._on_digit("5")),
             ("6", "num", lambda: self._on_digit("6")), ("-", "op", lambda: self._on_op("-"))],
            [("1", "num", lambda: self._on_digit("1")), ("2", "num", lambda: self._on_digit("2")),
             ("3", "num", lambda: self._on_digit("3")), ("+", "op", lambda: self._on_op("+"))],
            [("0", "num", lambda: self._on_digit("0")), (".", "num", self._on_decimal),
             ("=", "op", self._on_equals)],
        ]

        for r, row in enumerate(rows):
            c = 0
            for label, variant, handler in row:
                btn = CalcButton(label, variant=variant)
                btn.clicked.connect(handler)
                if label == "0":
                    grid.addWidget(btn, r, c, 1, 2)
                    c += 2
                else:
                    grid.addWidget(btn, r, c)
                    c += 1

        keypad_wrap = QWidget()
        keypad_wrap.setLayout(grid)
        self._card.expanded_layout.addWidget(keypad_wrap, 1)

        return self._card

    # --- accumulator logic -------------------------------------------------

    def _set_display(self, text):
        self._display = text
        for widget in (self._compact_display, self._expanded_display):
            if widget is not None:
                widget.setText(text)
        self._persist()

    def _current_value(self):
        try:
            return float(self._display)
        except ValueError:
            return 0.0

    def _on_digit(self, d):
        if self._display == "Error":
            self._fresh_entry = True
        if self._fresh_entry or self._display == "0":
            self._set_display(d)
            self._fresh_entry = False
        else:
            self._set_display(self._display + d)

    def _on_decimal(self):
        if self._fresh_entry or self._display == "Error":
            self._set_display("0.")
            self._fresh_entry = False
        elif "." not in self._display:
            self._set_display(self._display + ".")

    def _on_clear(self):
        self._stored_value = None
        self._pending_op = None
        self._fresh_entry = True
        self._set_display("0")

    def _on_sign(self):
        if self._display not in ("0", "Error"):
            if self._display.startswith("-"):
                self._set_display(self._display[1:])
            else:
                self._set_display("-" + self._display)

    def _on_percent(self):
        self._set_display(_format_number(self._current_value() / 100))
        self._fresh_entry = True

    def _apply_pending(self, next_value):
        if self._pending_op is None or self._stored_value is None:
            return next_value
        a, op = self._stored_value, self._pending_op
        try:
            if op == "+":
                return a + next_value
            if op == "-":
                return a - next_value
            if op == "*":
                return a * next_value
            if op == "/":
                if next_value == 0:
                    return None
                return a / next_value
        except OverflowError:
            return None
        return next_value

    def _on_op(self, op):
        current = self._current_value()
        if self._pending_op is not None and not self._fresh_entry:
            result = self._apply_pending(current)
            if result is None:
                self._set_display("Error")
                self._stored_value = None
                self._pending_op = None
                self._fresh_entry = True
                return
            self._stored_value = result
            self._set_display(_format_number(result))
        else:
            self._stored_value = current
        self._pending_op = op
        self._fresh_entry = True

    def _on_equals(self):
        current = self._current_value()
        result = self._apply_pending(current)
        if result is None:
            self._set_display("Error")
        else:
            self._set_display(_format_number(result))
        self._stored_value = None
        self._pending_op = None
        self._fresh_entry = True

    def on_collapse(self):
        self.flush_pending_saves()


register_module("calculator", CalculatorModule)
