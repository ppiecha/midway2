import sys

from PySide6.QtWidgets import QApplication

from constants import DARK_PALETTE
from gui.main_frame import MainFrame

if __name__ == '__main__':
    app = QApplication(sys.argv)
    app.setStyle('Fusion')  # Style needed for palette to work
    app.setPalette(DARK_PALETTE)
    frame = MainFrame(app=app)
    frame.show()
    sys.exit(app.exec())
