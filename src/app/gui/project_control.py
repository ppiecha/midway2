from __future__ import annotations

from typing import Dict, TYPE_CHECKING

from PySide6.QtCore import QSize
from PySide6.QtGui import Qt, QIcon
from PySide6.QtWidgets import QWidget, QTabWidget, QSplitter, QStackedWidget, QBoxLayout
from pubsub import pub

from src.app.gui.variant_grid import SingleVariantGrid, CompositionVariantGrid
from src.app.gui.track_list import TrackList
from src.app.gui.widgets import Box
from src.app.model.composition import Composition
from src.app.model.project import Project
from src.app.model.project_version import ProjectVersion
from src.app.utils.logger import get_console_logger

if TYPE_CHECKING:
    from src.app.gui.main_frame import MainFrame

logger = get_console_logger(__name__)


class ProjectControl(QWidget):
    def __init__(self, mf: MainFrame, parent, project: Project):
        super().__init__(parent=parent)
        self.mf = mf
        self.project = project
        self.map: Dict[str, TrackList] = {}
        self.tab_box = QTabWidget(self)
        for project_version in self.project.versions:
            self.new_project_version(project_version=project_version)
        self.main_box = Box(direction=QBoxLayout.TopToBottom)
        self.main_box.addWidget(self.tab_box)
        self.setLayout(self.main_box)

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
        track_list = self.map.pop(project_version.name)
        index = self.index_of_track_list(track_list=track_list)
        for track_id in list(track_list.map.keys()):
            track_list.delete_track(composition=composition, track=track_list[track_id].track)
        self.tab_box.removeTab(index)
        self.project.delete_composition(composition=composition)
        track_list.deleteLater()
        # self.tab_box.widget(index).deleteLater()

    def delete_all_compositions(self):
        for composition in list(self.project.versions):
            self.delete_project_version(composition=composition)

    @property
    def current_track_list(self) -> TrackList:
        vert_splitter: QSplitter = self.tab_box.currentWidget()
        tracks_splitter: QSplitter = vert_splitter.widget(0)
        track_list: TrackList = tracks_splitter.widget(0)
        if not track_list:
            raise ValueError("Cannot determine track list in current composition")
        return track_list

    def init_fonts(self):
        for track_list in self.map.values():
            for track_list_item in track_list.map.values():
                for track_version_detail_control in track_list_item.version_tab.map.values():
                    track_version_detail_control.track_item.init_fonts()

    def set_keyboard_position(self):
        for track_list in self.map.values():
            for track_list_item in track_list.map.values():
                for track_version_detail_control in track_list_item.version_tab.map.values():
                    track_version_detail_control.track_item.set_keyboard_position()

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
        # self.register_listeners()

    # def register_listeners(self):
    #     if not pub.subscribe(self.reload_tracks, GuiAttr.REFRESH_LOOPS):
    #         raise Exception(f"Cannot register listener {GuiAttr.REFRESH_LOOPS}")

    def reload_tracks(self, composition: Composition):
        if self.project_version == composition:
            self.single_variant_box.custom_loop_grid.load_loops()
            self.composition_variant_box.composition_loop_grid.load_loops()


class SingleVariantBox(QWidget):
    def __init__(self, mf, parent, project_version: ProjectVersion):
        super().__init__(parent=parent)
        self.main_box = Box(direction=QBoxLayout.LeftToRight)
        self.custom_loop_grid = SingleVariantGrid(parent=self, mf=mf, project_version=project_version)
        self.main_box.addWidget(self.custom_loop_grid, stretch=1)
        self.setLayout(self.main_box)


class CompositionVariantBox(QWidget):
    def __init__(self, mf, parent, project_version: ProjectVersion):
        super().__init__(parent=parent)
        self.main_box = Box(direction=QBoxLayout.TopToBottom)
        self.composition_loop_grid = CompositionVariantGrid(parent=self, mf=mf, project_version=project_version)
        self.main_box.addWidget(self.composition_loop_grid)
        self.setLayout(self.main_box)
