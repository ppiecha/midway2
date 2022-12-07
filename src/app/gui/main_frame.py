from __future__ import annotations
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
from src.app.model.serializer import read_json_file
from src.app.model.track import Track, TrackVersion
from src.app.model.types import dict_diff, DictDiff
from src.app.utils.logger import get_console_logger
from src.app.utils.notification import register_listener
from src.app.utils.properties import IniAttr, AppAttr, NotificationMessage, FileFilterAttr
from src.app.utils.file_system import file_exists, save_file_dialog

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
        self.project_control = ProjectControl(mf=self, parent=self)
        self._project: Optional[Project] = None
        self.project_file_name = None
        self.gen_config_dlg = GenericConfigDlg(mf=self)
        self.main_box = Box(direction=QBoxLayout.TopToBottom)
        self.main_box.addWidget(self.project_control)
        self.setLayout(self.main_box)
        self.central_widget = QWidget()  # define central widget
        self.setCentralWidget(self.central_widget)
        self.central_widget.setLayout(self.main_box)
        self.set_geometry()
        self.set_brand(project=self.project)

        register_listener(mapping={NotificationMessage.PROJECT_CHANGED: self.update_project_name})

        self.load_last_project()

    @property
    def project(self) -> Project:
        return self._project

    @project.setter
    def project(self, _project: Project):
        if _project is not None:
            self.project_control.project = _project
            self._project = _project

    @property
    def project_file_name(self):
        return self.project.file_name

    @project_file_name.setter
    def project_file_name(self, file_name: str):
        if file_name is None:
            self.project = empty_project()
            return
        if (result := file_exists(file_name=file_name)).error:
            self.show_message_box(message=result.error)
            self.project = empty_project()
            return
        if (result := Project.read_from_file(file_name=file_name)).error:
            self.show_message_box(message=f"<b>Cannot open project file</b> {file_name}", details=result.error)
            self.project = empty_project()
            return
        project = result.value
        project.file_name = file_name
        self.project = project

    def get_last_project_file_name(self) -> str:
        return self.config.value(IniAttr.PROJECT_FILE, "")

    def load_last_project(self):
        if (file_name := self.get_last_project_file_name()) != "":
            self.project_file_name = file_name

    def set_geometry(self):
        if self.config.value(IniAttr.MAIN_WINDOW_GEOMETRY, None) is not None:
            self.restoreGeometry(self.config.value(IniAttr.MAIN_WINDOW_GEOMETRY))
        else:
            self.setGeometry(
                QStyle.alignedRect(
                    Qt.LeftToRight,
                    Qt.AlignCenter,
                    self.size(),
                    self.screen().availableGeometry(),
                )
            )

    def showEvent(self, event: QShowEvent) -> None:
        super().showEvent(event)
        self.project_control.set_keyboard_position()

    def unsaved_changes(self) -> DictDiff:
        if self.project_file_name and Path(self.project_file_name).exists():
            last_saved_dict = read_json_file(json_file_name=self.project_file_name)
        else:
            last_saved_dict = {}
        diff = (diff for diff in dict_diff(d1=self.project.dict(), d2=last_saved_dict))
        diff_list = list(diff)
        if diff_list:
            logger.debug(self.project.dict())
            logger.debug(self.project.json())
            logger.debug(last_saved_dict)
        return DictDiff(d1=self.project.dict(), d2=last_saved_dict, diff=diff_list)

    def has_unsaved_changes(self) -> bool:
        if not self.project.versions:
            return False
        if (
            self.project_file_name
            and Path(self.project_file_name).exists()
            and not (result := read_json_file(json_file_name=self.project_file_name)).error
        ):
            last_saved_dict = result.value
        else:
            last_saved_dict = {}
        last_saved_project = Project(**last_saved_dict)
        current = self.project.json(exclude_none=True, exclude_defaults=True)
        last_saved = last_saved_project.json(exclude_none=True, exclude_defaults=True)
        return current != last_saved

    def save_config(self):
        self.config.setValue(IniAttr.MAIN_WINDOW_GEOMETRY, self.saveGeometry())
        self.config.setValue(IniAttr.PROJECT_FILE, self.project_file_name)

    def ask_about_changes(self) -> QMessageBox.StandardButton:
        return QMessageBox.question(
            self,
            "",
            "Project has unsaved changes<br><b>Save before exit?</b>",
            QMessageBox.Save | QMessageBox.Discard | QMessageBox.Cancel,
            QMessageBox.Cancel,
        )

    def get_save_file_name(self):
        return save_file_dialog(parent=self, dir_=AppAttr.PATH_PROJECT, filter_=FileFilterAttr.PROJECT)

    def save_project(self, file_name: str) -> QMessageBox.StandardButton:
        resp = QMessageBox.Ok
        if (error := self.project.save_to_file(file_name=file_name)) is not None:
            self.show_message_box(message=error)
            resp = QMessageBox.Cancel
        return resp

    def action_not_saved_changes(self) -> QMessageBox.StandardButton:
        resp = QMessageBox.Ok
        if self.has_unsaved_changes():
            if (resp := self.ask_about_changes()) == QMessageBox.Save:
                if not self.project_file_name:
                    if (file_name := self.get_save_file_name()) != "":
                        resp = self.save_project(file_name=file_name)
                    else:
                        resp = QMessageBox.Cancel
                else:
                    resp = self.save_project(file_name=self.project_file_name)
        return resp

    def closeEvent(self, event: QCloseEvent) -> None:
        if self.action_not_saved_changes() == QMessageBox.Cancel:
            event.ignore()
            return
        self.save_config()
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

    def set_brand(self, project: Project):
        self.update_project_name(project=project)
        self.setWindowIcon(QIcon(":/icons/midway.ico"))

    def update_project_name(self, project: Project):
        if project.name:
            name = f"{AppAttr.APP_NAME} - {project.name}"
        else:
            name = AppAttr.APP_NAME
        self.setWindowTitle(name)
        # self.app.setApplicationName(name)
        # self.app.setApplicationDisplayName(name)

    def show_config_dlg(self, config: GenericConfig):
        self.gen_config_dlg.load_config(config=config)
        self.gen_config_dlg.show()

    @property
    def current_track_list(self) -> Optional[TrackList]:
        return self.project_control.current_track_list

    @property
    def current_project_version(self) -> Optional[ProjectVersion]:
        return self.current_track_list.project_version if self.current_track_list else None

    @property
    def current_track_list_item(self) -> Optional[TrackListItem]:
        if not self.current_track_list:
            return None
        return self.current_track_list.current_track_list_item

    @property
    def current_track(self) -> Optional[Track]:
        if not self.current_track_list_item:
            return None
        return self.current_track_list_item.track if self.current_track_list else None

    @property
    def current_track_version(self) -> Optional[TrackVersion]:
        if not self.current_track_list_item:
            return None
        return self.current_track_list_item.current_track_version

    @property
    def current_track_version_control_tab(self) -> Optional[BaseTrackVersionControlTab]:
        if self.current_track_list and self.current_track_list_item:
            return self.current_track_list.current_track_list_item.current_track_version_control_tab
        return None

    def get_current_project_version_info(self) -> CurrentProjectVersionInfo:
        return CurrentProjectVersionInfo(
            project=self.project,
            project_version=self.current_project_version,
            track_list=self.current_track_list,
            track_list_item=self.current_track_list_item,
            track=self.current_track,
            track_version=self.current_track_version,
            track_version_control_tab=self.current_track_version_control_tab,
        )


class CurrentProjectVersionInfo(NamedTuple):
    project: Project
    project_version: ProjectVersion
    track_list: TrackList
    track_list_item: TrackListItem
    track: Track
    track_version: TrackVersion
    track_version_control_tab: BaseTrackVersionControlTab
