"""
core/edge_trigger.py

Right-edge hover detection with DPI awareness.

Qt screen geometry is in logical pixels; GetCursorPos returns physical.
We compare the physical cursor against a physical edge band, and the
logical cursor against a logical "inside" rect.
"""

import ctypes
import ctypes.wintypes as wintypes

from PySide6.QtCore import QObject, QTimer, Signal, QRect

HYSTERESIS_PX_LOGICAL = 40
DEBUG_POLLS = 20

class EdgeTrigger(QObject):
    edge_hit = Signal()
    left_zone = Signal()

    def __init__(self, screen_logical, device_pixel_ratio, open_geo_provider,
                 trigger_px=3, poll_ms=100, leave_grace_ms=350,
                 reopen_cooldown_ms=450, debug=False, parent=None):
        super().__init__(parent)
        self._screen = screen_logical
        self._dpr = max(1.0, float(device_pixel_ratio))
        self._open_geo_provider = open_geo_provider
        self._trigger_px = trigger_px
        self._is_open = False
        self._reopen_armed = True
        self._debug = debug
        self._debug_count = 0

        self._poll = QTimer(self)
        self._poll.setInterval(poll_ms)
        self._poll.timeout.connect(self._check_cursor)

        self._leave_timer = QTimer(self)
        self._leave_timer.setSingleShot(True)
        self._leave_timer.setInterval(leave_grace_ms)
        self._leave_timer.timeout.connect(self._confirm_leave)

        self._cooldown_timer = QTimer(self)
        self._cooldown_timer.setSingleShot(True)
        self._cooldown_timer.setInterval(reopen_cooldown_ms)
        self._cooldown_timer.timeout.connect(self._arm_reopen)

    def start(self):
        self._poll.start()

    def stop(self):
        self._poll.stop()

    def set_open(self, is_open):
        self._is_open = is_open
        if is_open:
            self._leave_timer.stop()
        else:
            self._reopen_armed = False
            self._cooldown_timer.start()

    def _arm_reopen(self):
        self._reopen_armed = True

    def _physical_edge_x(self):
        phys_width = int(round(self._screen.width() * self._dpr))
        return phys_width - self._trigger_px

    def _logical_inside_rect(self):
        return self._open_geo_provider().adjusted(-HYSTERESIS_PX_LOGICAL, 0, 0, 0)

    @staticmethod
    def _cursor_pos_physical():
        pt = wintypes.POINT()
        if not ctypes.windll.user32.GetCursorPos(ctypes.byref(pt)):
            return None
        return pt.x, pt.y

    def _check_cursor(self):
        phys = self._cursor_pos_physical()
        if phys is None:
            return
        px, py = phys
        lx = int(px / self._dpr)
        ly = int(py / self._dpr)

        if self._debug and self._debug_count < DEBUG_POLLS:
            self._debug_count += 1
            print(f"[edge] phys=({px},{py}) log=({lx},{ly}) dpr={self._dpr} "
                  f"edge_x={self._physical_edge_x()} open={self._is_open} armed={self._reopen_armed}")

        if not self._is_open:
            if not self._reopen_armed:
                return
            edge_x = self._physical_edge_x()
            if px >= edge_x and self._screen.top() <= ly <= self._screen.bottom():
                self.edge_hit.emit()
            return

        if self._logical_inside_rect().contains(lx, ly):
            self._leave_timer.stop()
        else:
            if not self._leave_timer.isActive():
                self._leave_timer.start()

    def _confirm_leave(self):
        phys = self._cursor_pos_physical()
        if phys is None:
            self.left_zone.emit()
            return
        px, py = phys
        lx = int(px / self._dpr)
        ly = int(py / self._dpr)
        if self._logical_inside_rect().contains(lx, ly):
            return
        self.left_zone.emit()
