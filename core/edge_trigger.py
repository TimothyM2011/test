"""
core/edge_trigger.py

Efficient right-edge hover detection.

We deliberately do NOT use a full-frequency global mouse hook running
Python callbacks on every OS mouse-move event (that wakes the
interpreter constantly and is wasteful for a "does nothing when
idle" app). Instead:

  - A QTimer polls cursor position at a modest interval (default 120ms)
  - The check itself is a single ctypes call (GetCursorPos) - cheap
  - We only care whether the cursor is within TRIGGER_WIDTH px of the
    right edge of the primary screen, and whether it's within the
    sidebar's vertical band once open (for hiding on leave)

120ms is imperceptible to the user for a "reach the edge, sidebar
appears" interaction, but is ~8 checks/sec instead of hundreds, and
each check is a single cheap syscall.
"""

import ctypes
from PySide6.QtCore import QObject, QTimer, Signal

TRIGGER_WIDTH = 4          # px from the right edge that counts as "hit"
POLL_INTERVAL_MS = 120      # how often we check cursor position
LEAVE_GRACE_MS = 300        # debounce before collapsing on mouse-leave


class EdgeTrigger(QObject):
    edge_hit = Signal()
    left_zone = Signal()

    def __init__(self, screen_geometry, sidebar_geometry_getter, parent=None):
        super().__init__(parent)
        self._screen_geo = screen_geometry
        self._get_sidebar_geo = sidebar_geometry_getter
        self._is_open = False
        self._pending_close = False

        self._poll_timer = QTimer(self)
        self._poll_timer.setInterval(POLL_INTERVAL_MS)
        self._poll_timer.timeout.connect(self._check_cursor)

        self._leave_timer = QTimer(self)
        self._leave_timer.setSingleShot(True)
        self._leave_timer.setInterval(LEAVE_GRACE_MS)
        self._leave_timer.timeout.connect(self._confirm_leave)

    def start(self):
        self._poll_timer.start()

    def stop(self):
        self._poll_timer.stop()

    def set_open(self, is_open: bool):
        self._is_open = is_open

    @staticmethod
    def _cursor_pos():
        pt = ctypes.wintypes.POINT() if hasattr(ctypes, "wintypes") else None
        try:
            import ctypes.wintypes as wintypes
            pt = wintypes.POINT()
            ctypes.windll.user32.GetCursorPos(ctypes.byref(pt))
            return pt.x, pt.y
        except Exception:
            # Non-Windows dev environment fallback (no-op)
            return None

    def _check_cursor(self):
        pos = self._cursor_pos()
        if pos is None:
            return
        x, y = pos

        if not self._is_open:
            edge_x = self._screen_geo.right() - TRIGGER_WIDTH
            if x >= edge_x:
                self.edge_hit.emit()
        else:
            geo = self._get_sidebar_geo()
            inside = geo.contains(x, y)
            if not inside:
                if not self._leave_timer.isActive():
                    self._leave_timer.start()
            else:
                self._leave_timer.stop()

    def _confirm_leave(self):
        self.left_zone.emit()
