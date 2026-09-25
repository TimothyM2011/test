"""
core/tray.py

No tray icon. Instead we register global hotkeys via the Win32 API
so the user can still quit and show/hide the sidebar without needing
a tray icon to right-click.

Hotkeys (registered on the sidebar's HWND):
    Ctrl+Alt+R  -> show sidebar
    Ctrl+Alt+H  -> hide sidebar
    Ctrl+Alt+Q  -> quit

Uses RegisterHotKey/UnregisterHotKey via ctypes and a Qt native event
filter to catch WM_HOTKEY (0x0312).
"""
import ctypes
import ctypes.wintypes as wintypes

from PySide6.QtCore import QAbstractNativeEventFilter
from PySide6.QtWidgets import QApplication

WM_HOTKEY = 0x0312
MOD_ALT = 0x0001
MOD_CONTROL = 0x0002
MOD_NOREPEAT = 0x4000

HOTKEY_SHOW = 1
HOTKEY_HIDE = 2
HOTKEY_QUIT = 3

class _HotkeyFilter(QAbstractNativeEventFilter):
    def __init__(self, handlers):
        super().__init__()
        self._handlers = handlers

    def nativeEventFilter(self, event_type, message):
        try:
            msg = ctypes.cast(int(message), ctypes.POINTER(wintypes.MSG)).contents
        except Exception:
            return False, 0
        if msg.message == WM_HOTKEY:
            handler = self._handlers.get(int(msg.wParam))
            if handler is not None:
                try:
                    handler()
                except Exception as e:
                    print(f"[hotkey] handler failed: {e}")
        return False, 0

def install_tray(app: QApplication, sidebar):
    """
    Kept the same function name as before so main.py does not need to
    change. Registers global hotkeys instead of creating a tray icon.
    """
    hwnd = int(sidebar.winId())

    user32 = ctypes.windll.user32

    if not user32.RegisterHotKey(hwnd, HOTKEY_SHOW,
                                 MOD_CONTROL | MOD_ALT | MOD_NOREPEAT, 0x52):  # R
        print("[hotkey] could not register Ctrl+Alt+R (already in use?)")
    if not user32.RegisterHotKey(hwnd, HOTKEY_HIDE,
                                 MOD_CONTROL | MOD_ALT | MOD_NOREPEAT, 0x48):  # H
        print("[hotkey] could not register Ctrl+Alt+H (already in use?)")
    if not user32.RegisterHotKey(hwnd, HOTKEY_QUIT,
                                 MOD_CONTROL | MOD_ALT | MOD_NOREPEAT, 0x51):  # Q
        print("[hotkey] could not register Ctrl+Alt+Q (already in use?)")

    handlers = {
        HOTKEY_SHOW: sidebar.open_sidebar,
        HOTKEY_HIDE: sidebar.close_sidebar,
        HOTKEY_QUIT: app.quit,
    }
    filt = _HotkeyFilter(handlers)
    app.installNativeEventFilter(filt)

    # Keep a reference so the filter is not garbage-collected.
    app._rightdock_hotkey_filter = filt
    app._rightdock_hwnd = hwnd
    return None
