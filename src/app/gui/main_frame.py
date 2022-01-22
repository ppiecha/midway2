import json
import os
from pathlib import Path
from typing import Optional

from PySide6.QtCore import QSettings, QSize, Qt
from PySide6.QtGui import QIcon, QShowEvent, QCloseEvent
from PySide6.QtWidgets import (
    QMainWindow,
    QBoxLayout,
    QWidget,
    QStyle,
    QApplication,
    QMessageBox,
)

from src.app.gui.composition_tab import CompositionTab
from src.app.gui.dialogs.generic_config import GenericConfigDlg, GenericConfig
from src.app.gui.menu import MenuBar
from src.app.gui.toolbar import ToolBar
from src.app.gui.widgets import Box
from src.app.backend.midway_synth import MidwaySynth
from src.app.model.project import Project, empty_project, simple_project
from src.app.utils.properties import IniAttr, AppAttr


class MainFrame(QMainWindow):
    def __init__(self, app: QApplication, config: QSettings):
        super().__init__()
        self.config = config
        self.synth = MidwaySynth(mf=self, sf2_path=AppAttr.PATH_SF2)
        self.status_bar = self.statusBar()
        self.app = app
        self.menu = MenuBar(self)
        self.setMenuBar(self.menu)
        self.addToolBar(ToolBar(self))
        self.project_file = self.config.value(
            IniAttr.PROJECT_FILE,
            os.path.join(AppAttr.PATH_SRC, IniAttr.PROJECT_TEMPLATE),
        )
        self.project: Optional[Project] = None
        if self.project_file and Path(self.project_file).exists():
            with open(self.project_file) as json_file:
                self.project = Project(**json.load(json_file))
        else:
            self.project = simple_project()
        self.gen_config_dlg = GenericConfigDlg(mf=self)
        self.composition_tab = CompositionTab(
            mf=self, parent=self, project=self.project
        )
        self.main_box = Box(direction=QBoxLayout.TopToBottom)
        self.main_box.addWidget(self.composition_tab)
        self.setLayout(self.main_box)
        self.central_widget = QWidget()  # define central widget
        self.setCentralWidget(self.central_widget)
        self.central_widget.setLayout(self.main_box)
        self.main_win_size = self.config.value(IniAttr.MAIN_WIN_SIZE, QSize(1000, 600))
        self.setGeometry(
            QStyle.alignedRect(
                Qt.LeftToRight,
                Qt.AlignCenter,
                self.size(),
                self.screen().availableGeometry(),
            )
        )
        self.set_brand()

    def showEvent(self, event: QShowEvent) -> None:
        super().showEvent(event)
        self.composition_tab.set_keyboard_position()

    def closeEvent(self, event: QCloseEvent) -> None:
        self.config.beginGroup(IniAttr.MAIN_WINDOW)
        self.config.setValue(IniAttr.MAIN_WIN_SIZE, self.size())
        self.config.setValue(IniAttr.MAIN_WIN_POS, self.pos())
        self.config.setValue(IniAttr.PROJECT_FILE, self.project_file)
        with open(self.project_file, "w", encoding="utf-8") as f:
            json.dump(
                self.project.dict(exclude=AppAttr.EXCLUDED_JSON_FIELDS),
                f,
                ensure_ascii=False,
                indent=2,
            )

    def show_message(self, message: str, timeout: int = 5000):
        self.status_bar.showMessage(message, timeout)

    def show_message_box(self, message: str):
        QMessageBox.information(self, "", message)

    def set_brand(self):
        self.setWindowTitle(AppAttr.APP_NAME)
        self.setWindowIcon(QIcon(":/icons/midway.ico"))
        self.app.setApplicationName(AppAttr.APP_NAME)
        self.app.setApplicationDisplayName(AppAttr.APP_NAME)

    def show_config_dlg(self, config: GenericConfig):
        self.gen_config_dlg.load_config(config=config)
        self.gen_config_dlg.show()
