from __future__ import annotations
import os
from pathlib import Path
from typing import Optional, NamedTuple

from PySide6.QtCore import QSettings, Qt
from PySide6.QtGui import QIcon, QShowEvent, QCloseEvent
from PySide6.QtWidgets import (
    QMainWindow,
    QBoxLayout,
    QWidget,
    QStyle,
    QApplication,
    QMessageBox,
)

from src.app.backend.midway_synth import MidwaySynth
from src.app.gui.project_control import ProjectControl
from src.app.gui.dialogs.generic_config import GenericConfigDlg, GenericConfig
from src.app.gui.menu import MenuBar
from src.app.gui.toolbar import ToolBar
from src.app.gui.track_control import BaseTrackVersionControlTab
from src.app.gui.track_list import TrackList, TrackListItem
from src.app.gui.widgets import Box
from src.app.model.project import Project, empty_project
from src.app.model.project_version import ProjectVersion
from src.app.model.serializer import read_json_file, write_json_file
from src.app.model.track import Track, TrackVersion
from src.app.model.types import dict_diff, DictDiff
from src.app.utils.logger import get_console_logger
from src.app.utils.properties import IniAttr, AppAttr

logger = get_console_logger(__name__)


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
            os.path.join(AppAttr.PATH_APP, IniAttr.DEFAULT_PROJECT),
        )
        self.project: Optional[Project] = None
        self.read_project_file(project_file_name=self.project_file)
        self.gen_config_dlg = GenericConfigDlg(mf=self)
        self.project_control = ProjectControl(mf=self, parent=self, project=self.project)
        self.main_box = Box(direction=QBoxLayout.TopToBottom)
        self.main_box.addWidget(self.project_control)
        self.setLayout(self.main_box)
        self.central_widget = QWidget()  # define central widget
        self.setCentralWidget(self.central_widget)
        self.central_widget.setLayout(self.main_box)
        self.set_geometry()
        self.set_brand()

    def set_geometry(self):
        if self.config.value(IniAttr.GEOMETRY, None) is not None:
            self.restoreGeometry(self.config.value(IniAttr.GEOMETRY))
        else:
            self.setGeometry(
                QStyle.alignedRect(
                    Qt.LeftToRight,
                    Qt.AlignCenter,
                    self.size(),
                    self.screen().availableGeometry(),
                )
            )

    def read_project_file(self, project_file_name: str):
        if project_file_name and Path(project_file_name).exists():
            self.project = Project(**read_json_file(json_file_name=project_file_name))
        else:
            self.show_message_box(
                message="Wrong last project file name or file doesn't exist", details=f"{project_file_name}"
            )
            self.project = empty_project()

    def save_project_file(self, project_file_name: str):
        write_json_file(
            json_dict=self.project.json(indent=2, exclude_none=True, exclude_defaults=True, exclude_unset=True),
            json_file_name=project_file_name,
        )

    def showEvent(self, event: QShowEvent) -> None:
        super().showEvent(event)
        self.project_control.set_keyboard_position()

    def unsaved_changes(self) -> DictDiff:
        if self.project_file and Path(self.project_file).exists():
            last_saved_dict = read_json_file(json_file_name=self.project_file)
        else:
            last_saved_dict = {}
        # last_saved_project = Project(**last_saved_dict)
        diff = (diff for diff in dict_diff(d1=self.project.dict(), d2=last_saved_dict))
        diff_list = list(diff)
        if diff_list:
            logger.debug(self.project.dict())
            logger.debug(self.project.json())
            logger.debug(last_saved_dict)
        return DictDiff(d1=self.project.dict(), d2=last_saved_dict, diff=diff_list)

    def has_unsaved_changes(self) -> bool:
        if self.project_file and Path(self.project_file).exists():
            last_saved_dict = read_json_file(json_file_name=self.project_file)
        else:
            last_saved_dict = {"name": "None"}
        last_saved_project = Project(**last_saved_dict)
        current = self.project.json(exclude_none=True, exclude_defaults=True, exclude_unset=True)
        last_saved = last_saved_project.json(exclude_none=True, exclude_defaults=True, exclude_unset=True)
        return current != last_saved

    def closeEvent(self, event: QCloseEvent) -> None:
        self.config.setValue(IniAttr.GEOMETRY, self.saveGeometry())
        self.config.setValue(IniAttr.PROJECT_FILE, self.project_file)
        if self.has_unsaved_changes():
            resp = QMessageBox.question(
                self,
                "",
                "Project has unsaved changes<br><b>Save before exit?</b>",
                QMessageBox.Save | QMessageBox.Discard | QMessageBox.Cancel,
                QMessageBox.Cancel,
            )
            if resp in (QMessageBox.Save, QMessageBox.Discard):
                if resp == QMessageBox.Save:
                    self.save_project_file(project_file_name=self.project_file)
                event.accept()
            if resp == QMessageBox.Cancel:
                event.ignore()
            return
        event.accept()

    def show_message(self, message: str, timeout: int = 5000):
        self.status_bar.showMessage(message, timeout)

    def show_message_box(
        self,
        message: str,
        details: str = None,
    ):
        if details:
            message = f"<b>{message}</b><br>{details}"
        QMessageBox.information(self, AppAttr.APP_NAME, message)

    def set_brand(self):
        self.setWindowTitle(AppAttr.APP_NAME)
        self.setWindowIcon(QIcon(":/icons/midway.ico"))
        self.app.setApplicationName(AppAttr.APP_NAME)
        self.app.setApplicationDisplayName(AppAttr.APP_NAME)

    def show_config_dlg(self, config: GenericConfig):
        self.gen_config_dlg.load_config(config=config)
        self.gen_config_dlg.show()

    @property
    def current_track_list(self) -> TrackList:
        return self.project_control.current_track_list

    @property
    def current_project_version(self) -> ProjectVersion:
        return self.current_track_list.project_version

    @property
    def current_track_list_item(self) -> TrackListItem:
        return self.current_track_list.current_track_list_item

    @property
    def current_track(self) -> Track:
        return self.current_track_list_item.track

    @property
    def current_track_version(self) -> TrackVersion:
        return self.current_track_list_item.current_track_version

    @property
    def current_track_version_control_tab(self) -> BaseTrackVersionControlTab:
        return self.current_track_list.current_track_list_item.current_track_version_control_tab

    def get_current_project_version_info(self) -> CurrentProjectVersionInfo:
        return CurrentProjectVersionInfo(
            project_version=self.current_project_version,
            track_list=self.current_track_list,
            track_list_item=self.current_track_list_item,
            track=self.current_track,
            track_version=self.current_track_version,
            track_version_control_tab=self.current_track_version_control_tab,
        )


class CurrentProjectVersionInfo(NamedTuple):
    project_version: ProjectVersion
    track_list: TrackList
    track_list_item: TrackListItem
    track: Track
    track_version: TrackVersion
    track_version_control_tab: BaseTrackVersionControlTab
