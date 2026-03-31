"""Application entrypoint (run as a module): python -m src_qt.main"""

from __future__ import annotations

import sys

from PyQt6.QtWidgets import QApplication

from .gui.main_window import MainWindow
from .gui.styles import DARK_APPLICATION_STYLESHEET


def main() -> None:
    app = QApplication(sys.argv)
    app.setStyleSheet(DARK_APPLICATION_STYLESHEET)
    win = MainWindow()
    win.show()
    sys.exit(app.exec())


if __name__ == "__main__":
    main()

