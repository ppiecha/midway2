import sys

from PySide6.QtWidgets import QApplication

from gui.main_frame import MainFrame
from src.app import config
from src.app.utils.properties import get_app_palette

if __name__ == "__main__":
    app = QApplication(sys.argv)
    app.setStyle("Fusion")  # Style needed for palette to work
    app.setPalette(get_app_palette())
    frame = MainFrame(app=app, config=config)
    frame.show()
    sys.exit(app.exec())
