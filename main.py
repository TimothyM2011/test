import sys
from PySide6.QtWidgets import QApplication
from core.window import Sidebar


def main():
    app = QApplication(sys.argv)
    app.setQuitOnLastWindowClosed(False)  # keep running when sidebar hides

    sidebar = Sidebar()  # noqa: F841 - kept alive by reference

    sys.exit(app.exec())


if __name__ == "__main__":
    main()
