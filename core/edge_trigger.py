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
# Small tolerance on the right/top/bottom edges of the "still inside"
# rect. Those edges sit flush against the physical screen boundary,
# and DPI rounding (int(px/dpr)) can nudge the computed logical cursor
# position by a pixel between polls even when the hand hasn't moved.
# Without this the sidebar reads "cursor left" on a stray poll, closes,
# and then immediately reopens once the cooldown clears - an on/off
# loop whenever the cursor rests right at the edge. This gives the
# rounding room to wobble without crossing the boundary.
EDGE_SLOP_PX_LOGICAL = 8
# Require this many consecutive "outside" polls before even starting
# the leave-grace timer, as a second line of defense against single
# noisy reads.
LEAVE_CONFIRM_POLLS = 2
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
        self._outside_streak = 0

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
        # Left side keeps the larger hysteresis (room to move away from
        # the panel without closing it). Right/top/bottom get a small
        # slop so DPI-rounding jitter at the physical screen boundary
        # can't read as "left the zone" on its own.
        return self._open_geo_provider().adjusted(
            -HYSTERESIS_PX_LOGICAL, -EDGE_SLOP_PX_LOGICAL,
            EDGE_SLOP_PX_LOGICAL, EDGE_SLOP_PX_LOGICAL,
        )

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
            self._outside_streak = 0
            self._leave_timer.stop()
        else:
            self._outside_streak += 1
            if self._outside_streak >= LEAVE_CONFIRM_POLLS and not self._leave_timer.isActive():
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
