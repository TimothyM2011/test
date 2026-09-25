"""
main.py
Entry point. Creates the QApplication, the sidebar, and a tray icon
so there's always a way to quit.
"""
import sys
from PySide6.QtWidgets import QApplication

from core.config import Config
from core.window import Sidebar
from core.tray import install_tray

def main():
    app = QApplication(sys.argv)
    app.setQuitOnLastWindowClosed(False)

    config = Config.load()
    sidebar = Sidebar(config)
    tray = install_tray(app, sidebar)  # noqa: F841

    sys.exit(app.exec())

if __name__ == "__main__":
    main()
