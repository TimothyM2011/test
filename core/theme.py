"""
core/theme.py
Single source of truth for colors + stylesheet. Change values here,
the whole app re-themes.
"""

ACCENT = "#6ad3ff"        # muted cyan accent
BG_WINDOW = "#1a1a1e"
BG_CARD = "#232328"
BG_CARD_HOVER = "#2a2a30"
BORDER = "#33333a"
TEXT_PRIMARY = "#e6e6e8"
TEXT_SECONDARY = "#9a9aa2"
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
"""
