from __future__ import annotations

from typing import Dict, TYPE_CHECKING, Optional, NamedTuple

from PySide6.QtCore import QSize
from PySide6.QtGui import Qt, QIcon
from PySide6.QtWidgets import QWidget, QTabWidget, QSplitter, QStackedWidget, QBoxLayout

from src.app.gui.variant_grid import SingleVariantGrid, CompositionVariantGrid
from src.app.gui.track_list import TrackList
from src.app.gui.widgets import Box
from src.app.model.composition import Composition
from src.app.model.project import Project
from src.app.model.project_version import ProjectVersion
from src.app.utils.logger import get_console_logger
from src.app.utils.notification import register_listener
from src.app.utils.properties import NotificationMessage

if TYPE_CHECKING:
    from src.app.gui.main_frame import MainFrame

logger = get_console_logger(__name__)


class ProjectVersionComponents(NamedTuple):
    track_list: TrackList
    grid_box: SequencerBox


class ProjectControl(QWidget):
    def __init__(self, mf: MainFrame, parent, project: Optional[Project] = None):
        super().__init__(parent=parent)
        self.mf = mf
        self._project: Optional[Project] = None
        self.map: Dict[str, TrackList] = {}
        self.tab_box = QTabWidget(self)
        self.main_box = Box(direction=QBoxLayout.TopToBottom)
        self.main_box.addWidget(self.tab_box)
        self.setLayout(self.main_box)

        self.project = project

        register_listener(
            mapping={
                NotificationMessage.PROJECT_VERSION_ADDED: self.new_project_version,
                NotificationMessage.PROJECT_VERSION_CHANGED: self.change_project_version_name,
                NotificationMessage.PROJECT_VERSION_REMOVED: self.delete_project_version,
            }
        )

    @property
    def project(self) -> Project:
        return self._project

    @project.setter
    def project(self, _project: Project):
        if _project is not None:
            if self._project is not None:
                self.delete_all_project_versions()
            self._project = _project
            self.create_project_versions(project=_project)

    def create_project_versions(self, project: Project):
        for project_version in project.versions:
            self.new_project_version(project_version=project_version)

    def change_project_version_name(self, old_version: ProjectVersion, new_version: ProjectVersion):
        index = self.index_by_project_version(project_version=old_version)
        self.tab_box.setTabText(index, new_version.name)

    def new_project_version(self, project_version: ProjectVersion):
        tracks_splitter = QSplitter(Qt.Horizontal)
        tracks_stack = QStackedWidget(self)
        self.map[project_version.name] = TrackList(
            mf=self.mf,
            parent=tracks_splitter,
            stack=tracks_stack,
            project_version=project_version,
        )
        tracks_splitter.addWidget(self.map[project_version.name])
        tracks_splitter.addWidget(tracks_stack)
        vert_splitter = QSplitter(Qt.Vertical)
        seq_box = SequencerBox(parent=vert_splitter, mf=self.mf, project_version=project_version)
        vert_splitter.addWidget(tracks_splitter)
        vert_splitter.addWidget(seq_box)
        vert_splitter.track_list = self.map[project_version.name]
        self.tab_box.addTab(vert_splitter, QIcon(":/icons/composition.png"), project_version.name)

    def index_of_track_list(self, track_list: TrackList) -> int:
        return self.tab_box.indexOf(track_list)

    def delete_project_version(self, project_version: ProjectVersion):
        index = self.index_by_project_version(project_version=project_version)
        track_list = self.map.pop(project_version.name)
        for track_id in list(track_list.map.keys()):
            track_list.delete_track(project_version=project_version, track=track_list[track_id].track)
        self.tab_box.widget(index).deleteLater()
        self.tab_box.removeTab(index)
        track_list.deleteLater()

    def delete_all_project_versions(self):
        for project_version in list(self.project.versions):
            self.delete_project_version(project_version=project_version)

    def index_by_project_version(self, project_version: ProjectVersion) -> int:
        track_list = self.map.get(project_version.name)
        if track_list is None:
            raise ValueError(f"Cannot determine track list by project version {project_version.name}")
        for i in range(self.tab_box.count()):
            if self.components_from_widget(widget=self.tab_box.widget(i)).track_list == track_list:
                return i
        raise ValueError(f"Cannot determine index by project_version {project_version.name}")

    def components_from_widget(self, widget: QSplitter | QWidget) -> ProjectVersionComponents:
        tracks_splitter: QSplitter = widget.widget(0)
        seq_box = widget.widget(1)
        track_list: TrackList = tracks_splitter.widget(0)
        if track_list is None:
            raise ValueError("Cannot determine track list in tab widget")
        return ProjectVersionComponents(track_list=track_list, grid_box=seq_box)

    def current_components(self) -> Optional[ProjectVersionComponents]:
        widget = self.tab_box.currentWidget()
        return self.components_from_widget(widget=widget) if widget else None

    @property
    def current_track_list(self) -> Optional[TrackList]:
        return components.track_list if (components := self.current_components()) is not None else None

    @property
    def current_grid_box(self) -> Optional[SequencerBox]:
        return components.grid_box if (components := self.current_components()) is not None else None

    def init_fonts(self):
        for track_list in self.map.values():
            for track_list_item in track_list.map.values():
                for track_version_detail_control in track_list_item.version_tab.map.values():
                    track_version_detail_control.track_version_control_tab.init_fonts()

    def set_keyboard_position(self):
        for track_list in self.map.values():
            for track_list_item in track_list.map.values():
                for track_version_detail_control in track_list_item.version_tab.map.values():
                    track_version_detail_control.track_version_control_tab.set_keyboard_position()

    @property
    def name(self) -> str:
        return self.project.name

    @name.setter
    def name(self, value: str) -> None:
        self.project.name = value

    def __iter__(self):
        return iter(self.map)

    def __getitem__(self, composition: str) -> TrackList:
        track_list = self.map.get(composition)
        if track_list is None:
            raise IndexError
        return track_list

    def __len__(self):
        return len(self.map)


class SequencerBox(QWidget):
    def __init__(self, mf, parent, project_version: ProjectVersion):
        super().__init__(parent=parent)
        self.project_version = project_version
        self.splitter = QSplitter(Qt.Horizontal)
        self.single_variant_box = SingleVariantBox(parent=self.splitter, mf=mf, project_version=project_version)
        self.splitter.addWidget(self.single_variant_box)
        self.composition_variant_box = CompositionVariantBox(
            parent=self.splitter, mf=mf, project_version=project_version
        )
        self.splitter.addWidget(self.composition_variant_box)
        self.main_box = Box(direction=QBoxLayout.TopToBottom)
        # self.main_box.setContentsMargins(5, 5, 5, 5)
        self.main_box.setSpacing(5)
        self.main_box.addWidget(self.splitter)
        self.setLayout(self.main_box)
        self.resize(QSize(self.width(), 400))

    def reload_tracks(self, composition: Composition):
        if self.project_version == composition:
            self.single_variant_box.grid.load_items()
            self.composition_variant_box.grid.load_items()


class SingleVariantBox(QWidget):
    def __init__(self, mf, parent, project_version: ProjectVersion):
        super().__init__(parent=parent)
        self.main_box = Box(direction=QBoxLayout.LeftToRight)
        self.grid = SingleVariantGrid(parent=self, mf=mf, project_version=project_version)
        self.main_box.addWidget(self.grid, stretch=1)
        self.setLayout(self.main_box)


class CompositionVariantBox(QWidget):
    def __init__(self, mf, parent, project_version: ProjectVersion):
        super().__init__(parent=parent)
        self.main_box = Box(direction=QBoxLayout.TopToBottom)
        self.grid = CompositionVariantGrid(parent=self, mf=mf, project_version=project_version)
        self.main_box.addWidget(self.grid)
        self.setLayout(self.main_box)
