"""
core/window.py

The sidebar window itself:
  - Frameless, always-on-top, anchored to the right screen edge
  - Slides in/out with a parallel opacity fade (both animated
    together so the panel feels like it eases in rather than
    "sliding then appearing")
  - Fully collapses off-screen when hidden (not just invisible) so
    it costs nothing while idle
  - Talks to EdgeTrigger for show/hide and TickDispatcher for the
    two-tier refresh model
"""

from PySide6.QtWidgets import QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton
from PySide6.QtCore import Qt, QPropertyAnimation, QEasingCurve, QRect, QParallelAnimationGroup
from PySide6.QtGui import QGuiApplication

from core.theme import STYLESHEET
from core.widgets import Card, MetricRow
from core.tick_dispatcher import TickDispatcher
from core.edge_trigger import EdgeTrigger
from modules.hardware import hardware

SIDEBAR_WIDTH = 300
ANIM_DURATION_MS = 220


class Sidebar(QWidget):
    def __init__(self):
        super().__init__()
        self._build_window_flags()
        self.setStyleSheet(STYLESHEET)

        screen = QGuiApplication.primaryScreen().geometry()
        self._screen_geo = screen
        self.setFixedSize(SIDEBAR_WIDTH, screen.height())

        # Start fully off-screen to the right, invisible
        self._closed_geo = QRect(screen.right(), 0, SIDEBAR_WIDTH, screen.height())
        self._open_geo = QRect(screen.right() - SIDEBAR_WIDTH, 0, SIDEBAR_WIDTH, screen.height())
        self.setGeometry(self._closed_geo)

        self._build_ui()
        self._build_animation()

        self.dispatcher = TickDispatcher(self)
        self._register_modules()

        self.edge = EdgeTrigger(screen, lambda: self.geometry(), self)
        self.edge.edge_hit.connect(self.open_sidebar)
        self.edge.left_zone.connect(self.close_sidebar)
        self.edge.start()

        self._is_open = False
        self.hide()  # truly unmapped, not just transparent

    # ---------------------------------------------------------- window setup
    def _build_window_flags(self):
        self.setWindowFlags(
            Qt.FramelessWindowHint
            | Qt.WindowStaysOnTopHint
            | Qt.Tool  # no taskbar entry
        )
        self.setAttribute(Qt.WA_TranslucentBackground, False)

    def _build_ui(self):
        root = QVBoxLayout(self)
        root.setContentsMargins(0, 0, 0, 0)
        root.setSpacing(0)
        self.setObjectName("SidebarRoot")

        header = QWidget()
        header.setObjectName("HeaderBar")
        header.setFixedHeight(44)
        h_layout = QHBoxLayout(header)
        h_layout.setContentsMargins(16, 0, 12, 0)

        title = QLabel("RIGHTSIDE")
        title.setObjectName("HeaderTitle")
        settings_btn = QPushButton("⚙")
        settings_btn.setFixedSize(28, 28)

        h_layout.addWidget(title)
        h_layout.addStretch()
        h_layout.addWidget(settings_btn)
        root.addWidget(header)

        content = QWidget()
        self.content_layout = QVBoxLayout(content)
        self.content_layout.setContentsMargins(14, 14, 14, 14)
        self.content_layout.setSpacing(12)
        self.content_layout.addStretch()
        root.addWidget(content)

        # Hardware card (first module wired up end-to-end)
        self.hw_card = Card("System")
        self.cpu_row = MetricRow("CPU")
        self.ram_row = MetricRow("RAM")
        self.gpu_row = MetricRow("GPU")
        self.hw_card.body.addWidget(self.cpu_row)
        self.hw_card.body.addWidget(self.ram_row)
        self.hw_card.body.addWidget(self.gpu_row)
        self.content_layout.insertWidget(0, self.hw_card)

        # Opacity effect target = whole window content
        from PySide6.QtWidgets import QGraphicsOpacityEffect
        self._opacity_effect = QGraphicsOpacityEffect(self)
        self.setGraphicsEffect(self._opacity_effect)
        self._opacity_effect.setOpacity(0.0)

    def _build_animation(self):
        self._pos_anim = QPropertyAnimation(self, b"geometry")
        self._pos_anim.setDuration(ANIM_DURATION_MS)
        self._pos_anim.setEasingCurve(QEasingCurve.OutCubic)

        self._opacity_anim = QPropertyAnimation(self._opacity_effect, b"opacity")
        self._opacity_anim.setDuration(ANIM_DURATION_MS)
        self._opacity_anim.setEasingCurve(QEasingCurve.OutCubic)

        self._group = QParallelAnimationGroup(self)
        self._group.addAnimation(self._pos_anim)
        self._group.addAnimation(self._opacity_anim)

    # ---------------------------------------------------------- modules
    def _register_modules(self):
        self.dispatcher.register(
            "hardware_cheap",
            self._refresh_hardware_cheap,
            cheap=True,
        )
        self.dispatcher.register(
            "hardware_full",
            self._refresh_hardware_full,
            cheap=False,
            expanded_every=1,
        )

    def _refresh_hardware_cheap(self):
        # Runs every 5 min while collapsed - no UI paint needed since
        # nothing is visible, but we keep the values warm so the
        # instant-open refresh has less to catch up on.
        self._last_stats = hardware.read_cheap_stats()

    def _refresh_hardware_full(self):
        stats = hardware.read_full_stats()
        self._last_stats = stats
        self.cpu_row.set_value(stats.get("cpu_percent"))
        self.ram_row.set_value(stats.get("ram_percent"))
        self.gpu_row.set_value(stats.get("gpu_percent"))

    # ---------------------------------------------------------- open/close
    def open_sidebar(self):
        if self._is_open:
            return
        self._is_open = True
        self.edge.set_open(True)

        self.show()
        self.dispatcher.on_expand()  # immediate full refresh, then fast tier

        self._group.stop()
        self._pos_anim.setStartValue(self._closed_geo)
        self._pos_anim.setEndValue(self._open_geo)
        self._opacity_anim.setStartValue(0.0)
        self._opacity_anim.setEndValue(1.0)
        self._group.start()

    def close_sidebar(self):
        if not self._is_open:
            return
        self._is_open = False
        self.edge.set_open(False)
        self.dispatcher.on_collapse()

        self._group.stop()
        self._pos_anim.setStartValue(self.geometry())
        self._pos_anim.setEndValue(self._closed_geo)
        self._opacity_anim.setStartValue(1.0)
        self._opacity_anim.setEndValue(0.0)
        self._group.finished.connect(self._on_close_finished)
        self._group.start()

    def _on_close_finished(self):
        self._group.finished.disconnect(self._on_close_finished)
        self.hide()  # fully unmap - zero paint cost while collapsed
