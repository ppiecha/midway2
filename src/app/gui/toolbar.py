from PySide6.QtCore import QSize, Qt
from PySide6.QtWidgets import QToolBar

from src.app.utils.constants import NEW_PROJECT
from src.app.gui.menu import MenuBar


class ToolBar(QToolBar):
    def __init__(self, parent):
        super().__init__("Main toolbar", parent)
        self.setToolButtonStyle(Qt.ToolButtonIconOnly)
        self.setIconSize(QSize(16, 16))
        self.menu: MenuBar = parent.menuBar()
        self.addAction(self.menu.actions[NEW_PROJECT])
