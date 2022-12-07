from __future__ import annotations

import sys

from PySide6.QtWidgets import QApplication

from src.app.gui.main_frame import MainFrame
from src.app import config
from src.app.utils.properties import get_app_palette

if __name__ == "__main__":
    app = QApplication(sys.argv)
    app.setStyle("Fusion")  # Style needed for palette to work
    app.setPalette(get_app_palette())
    mf = MainFrame(app=app, config=config)
    mf.show()
    sys.exit(app.exec())
