import json
from pathlib import Path
from typing import Optional

from PySide6.QtCore import QSettings, QSize, Qt
from PySide6.QtGui import QIcon, QShowEvent, QCloseEvent
from PySide6.QtWidgets import QMainWindow, QBoxLayout, QWidget, QStyle, \
    QApplication, QMessageBox

from src.app.utils.constants import SRC_PATH, APP_NAME, SF2_PATH, PROJECT_FILE, \
    MAIN_WIN_SIZE, MAIN_WIN_POS
from src.app.gui.composition_tab import CompositionTab
from src.app.gui.dialogs.generic_config import GenericConfigDlg, GenericConfig
from src.app.gui.menu import MenuBar
from src.app.gui.toolbar import ToolBar
from src.app.gui.widgets import Box
from src.app.backend.synth import FS
from src.app.model.project import Project, sample_project


class MainFrame(QMainWindow):
    def __init__(self, app: QApplication, config_file: str = 'config.ini'):
        super().__init__()
        self.synth = FS(mf=self, sf2_path=SF2_PATH)
        self.status_bar = self.statusBar()
        self.app = app
        self.menu = MenuBar(self)
        self.setMenuBar(self.menu)
        self.addToolBar(ToolBar(self))
        self.config = QSettings(config_file, QSettings.IniFormat)
        self.project_file: str = self.config.value('project_file',
                                                   str(Path(SRC_PATH).joinpath(
                                                       "default.json")))
        self.project: Optional[Project] = None
        if self.project_file and Path(self.project_file).exists():
            with open(self.project_file) as json_file:
                self.project = Project(**json.load(json_file))
        else:
            self.project = sample_project()
        self.gen_config_dlg = GenericConfigDlg(mf=self)
        self.composition_tab = CompositionTab(mf=self, parent=self,
                                              project=self.project)
        self.main_box = Box(direction=QBoxLayout.TopToBottom)
        self.main_box.addWidget(self.composition_tab)
        self.setLayout(self.main_box)
        self.central_widget = QWidget()  # define central widget
        self.setCentralWidget(self.central_widget)
        self.central_widget.setLayout(self.main_box)
        self.resize(self.config.value(MAIN_WIN_SIZE, QSize(1000, 600)))
        self.setGeometry(
            QStyle.alignedRect(Qt.LeftToRight, Qt.AlignCenter, self.size(),
                               self.screen().availableGeometry()))
        self.set_brand()

    def showEvent(self, event: QShowEvent) -> None:
        super().showEvent(event)
        self.composition_tab.set_keyboard_position()

    def closeEvent(self, event: QCloseEvent) -> None:
        self.config.setValue(MAIN_WIN_SIZE, self.size())
        self.config.setValue(MAIN_WIN_POS, self.pos())
        self.config.setValue(PROJECT_FILE, self.project_file)
        with open(self.project_file, "w", encoding="utf-8") as f:
            json.dump(self.project.dict(), f, ensure_ascii=False, indent=2)

    def show_message(self, message: str, timeout: int = 5000):
        self.status_bar.showMessage(message, timeout)

    def show_message_box(self, message: str):
        QMessageBox.information(self, '', message)

    def set_brand(self):
        self.setWindowTitle(APP_NAME)
        self.setWindowIcon(QIcon(":/icons/midway.ico"))
        self.app.setApplicationName(APP_NAME)
        self.app.setApplicationDisplayName(APP_NAME)

    def show_config_dlg(self, config: GenericConfig):
        self.gen_config_dlg.load_config(config=config)
        self.gen_config_dlg.show()
