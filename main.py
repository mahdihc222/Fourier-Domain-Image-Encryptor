import sys
from PySide6.QtWidgets import QApplication

from ui.main_window import MainWindow
from ui.styles import MAIN_STYLESHEET


def main():
    app = QApplication(sys.argv)
    app.setStyleSheet(MAIN_STYLESHEET)

    window = MainWindow()
    window.show()
    sys.exit(app.exec())


if __name__ == "__main__":
    main()