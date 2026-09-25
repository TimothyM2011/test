"""
core/theme.py
Single source of truth for colors + stylesheet.
"""

ACCENT = "#6ad3ff"
BG_WINDOW = "#1a1a1e"
BG_CARD = "#232328"
BG_CARD_HOVER = "#2a2a30"
BORDER = "#33333a"
TEXT_PRIMARY = "#e6e6e8"
TEXT_SECONDARY = "#9a9aa2"
TEXT_MUTED = "#6b6b74"
DANGER = "#ff6b6b"

RADIUS = 10

STYLESHEET = f"""
QWidget {{
    background-color: {BG_WINDOW};
    color: {TEXT_PRIMARY};
    font-family: 'Segoe UI', sans-serif;
    font-size: 13px;
}}

#SidebarRoot {{
    background-color: {BG_WINDOW};
    border-left: 1px solid {BORDER};
}}

#HeaderBar {{
    background-color: transparent;
    border-bottom: 1px solid {BORDER};
}}

#HeaderTitle {{
    color: {TEXT_PRIMARY};
    font-size: 13px;
    font-weight: 600;
    letter-spacing: 1px;
}}

.Card {{
    background-color: {BG_CARD};
    border: 1px solid {BORDER};
    border-radius: {RADIUS}px;
}}

.Card:hover {{
    background-color: {BG_CARD_HOVER};
}}

.CardTitle {{
    color: {TEXT_SECONDARY};
    font-size: 11px;
    font-weight: 600;
    letter-spacing: 1.5px;
}}

QProgressBar {{
    background-color: #16161a;
    border: none;
    border-radius: 4px;
    height: 6px;
    text-align: center;
}}

QProgressBar::chunk {{
    background-color: {ACCENT};
    border-radius: 4px;
}}

QPushButton {{
    background-color: {BG_CARD};
    border: 1px solid {BORDER};
    border-radius: 6px;
    padding: 6px 10px;
    color: {TEXT_PRIMARY};
}}

QPushButton:hover {{
    background-color: {BG_CARD_HOVER};
    border-color: {ACCENT};
}}

QPushButton:pressed {{
    background-color: #1c1c20;
}}

QPushButton#DangerButton:hover {{
    border-color: {DANGER};
    color: {DANGER};
}}

QLineEdit, QPlainTextEdit, QTextEdit, QDateEdit {{
    background-color: #16161a;
    border: 1px solid {BORDER};
    border-radius: 6px;
    padding: 5px 8px;
    color: {TEXT_PRIMARY};
    selection-background-color: {ACCENT};
    selection-color: #101014;
}}

QLineEdit:focus, QPlainTextEdit:focus, QTextEdit:focus, QDateEdit:focus {{
    border-color: {ACCENT};
}}

QCheckBox {{
    spacing: 8px;
}}

QCheckBox::indicator {{
    width: 14px;
    height: 14px;
    border-radius: 3px;
    border: 1px solid {BORDER};
    background-color: #16161a;
}}

QCheckBox::indicator:checked {{
    background-color: {ACCENT};
    border-color: {ACCENT};
}}

QListWidget {{
    background-color: #16161a;
    border: 1px solid {BORDER};
    border-radius: 6px;
    padding: 4px;
}}

QListWidget::item {{
    padding: 6px 8px;
    border-radius: 4px;
}}

QListWidget::item:selected {{
    background-color: {BG_CARD_HOVER};
    color: {TEXT_PRIMARY};
}}

QListWidget::item:hover {{
    background-color: #1f1f24;
}}

QScrollBar:vertical {{
    background: transparent;
    width: 6px;
}}

QScrollBar::handle:vertical {{
    background: {BORDER};
    border-radius: 3px;
    min-height: 24px;
}}

QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {{
    height: 0px;
}}

QScrollBar:horizontal {{
    background: transparent;
    height: 6px;
}}

QScrollBar::handle:horizontal {{
    background: {BORDER};
    border-radius: 3px;
    min-width: 24px;
}}

QScrollBar::add-line:horizontal, QScrollBar::sub-line:horizontal {{
    width: 0px;
}}
"""
