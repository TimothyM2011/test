"""
core/window.py

Frameless, always-on-top sidebar anchored to the right screen edge.

Reads config.modules and instantiates each module in order. Width
animates between sidebar_width and expanded_width as modules request
expand/collapse.
"""
from PySide6.QtWidgets import QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton
from PySide6.QtCore import Qt, QPropertyAnimation, QEasingCurve, QRect
from PySide6.QtGui import QGuiApplication

from core.config import Config
from core.theme import STYLESHEET
from core.state import StateStore
from core.tick_dispatcher import TickDispatcher
from core.edge_trigger import EdgeTrigger
from core.widgets import ExpandedCard

class Sidebar(QWidget):
    def __init__(self, config: Config):
        super().__init__()
        self.config = config
        self._is_open = False
        self._current_width = config.sidebar_width
        self._expanded_modules = set()

        self._build_window_flags()
        self.setStyleSheet(STYLESHEET)

        primary = QGuiApplication.primaryScreen()
        screen = primary.geometry()
        dpr = primary.devicePixelRatio()
        self._screen = screen
        self._dpr = dpr

        self.setFixedSize(self._current_width, screen.height())

        self._closed_geo = QRect(screen.right(), screen.top(),
                                 self._current_width, screen.height())
        self._open_geo = QRect(screen.right() - self._current_width, screen.top(),
                               self._current_width, screen.height())
        self.setGeometry(self._closed_geo)

        self.state_store = StateStore(config.state_path)
        self.dispatcher = TickDispatcher(self)

        self._modules = []
        self._module_widgets = {}

        self._build_ui()
        self._build_animation()
        self._build_modules()
        self._register_module_ticks()

        self.edge = EdgeTrigger(
            screen_logical=screen,
            device_pixel_ratio=dpr,
            open_geo_provider=self._current_open_geo,
            trigger_px=config.edge_trigger_px,
            poll_ms=config.poll_ms,
            leave_grace_ms=config.leave_grace_ms,
            reopen_cooldown_ms=config.reopen_cooldown_ms,
            debug=config.debug_edge,
            parent=self,
        )
        self.edge.edge_hit.connect(self.open_sidebar)
        self.edge.left_zone.connect(self.close_sidebar)
        self.edge.start()

        self.hide()

    def _current_open_geo(self):
        return QRect(self._screen.right() - self._current_width,
                     self._screen.top(),
                     self._current_width,
                     self._screen.height())

    def _current_closed_geo(self):
        return QRect(self._screen.right(),
                     self._screen.top(),
                     self._current_width,
                     self._screen.height())

    def _build_window_flags(self):
        self.setWindowFlags(
            Qt.FramelessWindowHint
            | Qt.WindowStaysOnTopHint
            | Qt.Tool
        )

    def _build_ui(self):
        root = QVBoxLayout(self)
        root.setContentsMargins(0, 0, 0, 0)
        root.setSpacing(0)
        self.setObjectName("SidebarRoot")

        header = QWidget()
        header.setObjectName("HeaderBar")
        header.setFixedHeight(44)
        h = QHBoxLayout(header)
        h.setContentsMargins(16, 0, 12, 0)

        title = QLabel("RIGHTSIDE")
        title.setObjectName("HeaderTitle")
        settings_btn = QPushButton("g")
        settings_btn.setFixedSize(28, 28)

        h.addWidget(title)
        h.addStretch()
        h.addWidget(settings_btn)
        root.addWidget(header)

        content = QWidget()
        self.content_layout = QVBoxLayout(content)
        self.content_layout.setContentsMargins(14, 14, 14, 14)
        self.content_layout.setSpacing(12)
        self.content_layout.addStretch()
        root.addWidget(content, 1)

    def _build_animation(self):
        self._pos_anim = QPropertyAnimation(self, b"geometry")
        self._pos_anim.setDuration(self.config.anim_ms)
        self._pos_anim.setEasingCurve(QEasingCurve.OutCubic)
        self._pos_anim.finished.connect(self._on_anim_finished)

    def _instantiate_module(self, module_id):
        if module_id == "hardware":
            from modules.hardware.module import HardwareModule
            return HardwareModule(self.config, self.state_store, host=self)
        if module_id == "notes":
            from modules.notes.notes import NotesModule
            return NotesModule(self.config, self.state_store, host=self)
        if module_id == "tasks":
            from modules.tasks.tasks import TasksModule
            return TasksModule(self.config, self.state_store, host=self)
        if module_id == "timers":
            from modules.timers.clock import ClockModule
            return ClockModule(self.config, self.state_store, host=self)
        print(f"[window] unknown module id: {module_id}")
        return None

    def _build_modules(self):
        for module_id in self.config.modules:
            mod = self._instantiate_module(module_id)
            if mod is None:
                continue
            widget = mod.widget()
            self._modules.append(mod)
            self._module_widgets[mod.id] = widget

            card = widget if isinstance(widget, ExpandedCard) else None
            if card is None:
                card = widget.findChild(ExpandedCard)
            if card is not None:
                card.expand_requested.connect(
                    lambda _=False, mid=mod.id: self.request_expand(mid))
                card.collapse_requested.connect(
                    lambda _=False, mid=mod.id: self.request_collapse(mid))

            idx = self.content_layout.count() - 1
            self.content_layout.insertWidget(idx, widget)

    def _register_module_ticks(self):
        for mod in self._modules:
            self.dispatcher.register(
                f"module::{mod.id}",
                mod.on_tick,
                cheap=getattr(mod, "cheap_tick", False),
                expanded_every=getattr(mod, "expanded_every", 1),
            )

    def request_expand(self, module_id):
        if module_id in self._expanded_modules:
            return
        self._expanded_modules.add(module_id)
        self._apply_module_visual_state(module_id, True)
        if self._is_open:
            self._animate_to_width(self.config.expanded_width)

    def request_collapse(self, module_id):
        if module_id not in self._expanded_modules:
            return
        self._expanded_modules.discard(module_id)
        self._apply_module_visual_state(module_id, False)
        if not self._expanded_modules and self._is_open:
            self._animate_to_width(self.config.sidebar_width)

    def _apply_module_visual_state(self, module_id, expanded):
        widget = self._module_widgets.get(module_id)
        if widget is None:
            return
        card = widget if isinstance(widget, ExpandedCard) else widget.findChild(ExpandedCard)
        if card is not None:
            card.set_expanded(expanded)
        mod = next((m for m in self._modules if m.id == module_id), None)
        if mod is not None:
            if expanded:
                mod.on_expand()
            else:
                mod.on_collapse()

    def _animate_to_width(self, target_width):
        if target_width == self._current_width:
            return
        self._current_width = target_width
        self.setFixedSize(target_width, self._screen.height())
        start = self.geometry()
        target = QRect(self._screen.right() - target_width,
                       self._screen.top(),
                       target_width,
                       self._screen.height())
        self._pos_anim.stop()
        self._pos_anim.setStartValue(start)
        self._pos_anim.setEndValue(target)
        self._pos_anim.start()

    def open_sidebar(self):
        if self._is_open:
            return
        self._is_open = True
        self.edge.set_open(True)

        self.show()
        self.raise_()
        self.dispatcher.on_expand()

        for mod in self._modules:
            mod.flush_pending_saves()

        for mid in list(self._expanded_modules):
            self._apply_module_visual_state(mid, True)

        self._pos_anim.stop()
        self._pos_anim.setStartValue(self._current_closed_geo())
        self._pos_anim.setEndValue(self._current_open_geo())
        self._pos_anim.start()

    def close_sidebar(self):
        if not self._is_open:
            return
        self._is_open = False
        self.edge.set_open(False)
        self.dispatcher.on_collapse()

        for mod in self._modules:
            mod.flush_pending_saves()

        self._pos_anim.stop()
        self._pos_anim.setStartValue(self.geometry())
        self._pos_anim.setEndValue(self._current_closed_geo())
        self._pos_anim.start()

    def _on_anim_finished(self):
        if not self._is_open:
            self.hide()
