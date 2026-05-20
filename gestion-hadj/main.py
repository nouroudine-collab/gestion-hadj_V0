import sys

from PySide6.QtWidgets import QApplication

from database.db import init_db
from UIs.main_window import MainWindow


def main() -> int:
    init_db()
    app = QApplication(sys.argv)
    app.setStyleSheet(open("assets/styles/global.qss", encoding="utf-8").read())
    window = MainWindow()
    window.show()
    return app.exec()


if __name__ == "__main__":
    raise SystemExit(main())