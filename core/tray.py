"""
core/tray.py

Tray icon with a Quit action. Without this, a misbehaving sidebar
would require Task Manager to kill.
"""
from PySide6.QtWidgets import QSystemTrayIcon, QMenu, QStyle
from PySide6.QtGui import QAction

def install_tray(app, sidebar) -> QSystemTrayIcon:
    tray = QSystemTrayIcon(app)
    icon = app.style().standardIcon(QStyle.SP_ComputerIcon)
    tray.setIcon(icon)
    tray.setToolTip("RightSide")

    menu = QMenu()

    open_action = QAction("Show sidebar")
    open_action.triggered.connect(sidebar.open_sidebar)
    menu.addAction(open_action)

    hide_action = QAction("Hide sidebar")
    hide_action.triggered.connect(sidebar.close_sidebar)
    menu.addAction(hide_action)

    menu.addSeparator()

    quit_action = QAction("Quit")
    quit_action.triggered.connect(app.quit)
    menu.addAction(quit_action)

    tray.setContextMenu(menu)
    tray.show()
    return tray
