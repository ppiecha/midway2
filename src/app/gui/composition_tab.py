from __future__ import annotations
from typing import Dict

from PySide6.QtCore import QSize
from PySide6.QtGui import Qt, QIcon
from PySide6.QtWidgets import QWidget, QTabWidget, QSplitter, QStackedWidget, QBoxLayout
from pubsub import pub

from src.app.gui.sequence_grid import CustomLoopGrid, CompositionLoopGrid
from src.app.gui.track_list import TrackList
from src.app.gui.widgets import Box
from src.app.model.composition import Composition
from src.app.model.project import Project
from typing import TYPE_CHECKING

from src.app.utils.properties import GuiAttr

if TYPE_CHECKING:
    from src.app.gui.main_frame import MainFrame


class CompositionTab(QWidget):
    def __init__(self, mf: MainFrame, parent, project: Project):
        super().__init__(parent=parent)
        self.mf = mf
        self.project = project
        self.map: Dict[str, TrackList] = {}
        self.tab_box = QTabWidget(self)
        for composition in self.project.compositions:
            self.new_composition(composition=composition)
        self.main_box = Box(direction=QBoxLayout.TopToBottom)
        self.main_box.addWidget(self.tab_box)
        self.setLayout(self.main_box)

    def new_composition(self, composition: Composition):
        tracks_splitter = QSplitter(Qt.Horizontal)
        tracks_stack = QStackedWidget(self)
        self.map[composition.name] = TrackList(
            mf=self.mf,
            parent=tracks_splitter,
            stack=tracks_stack,
            composition=composition,
        )
        tracks_splitter.addWidget(self.map[composition.name])
        tracks_splitter.addWidget(tracks_stack)
        vert_splitter = QSplitter(Qt.Vertical)
        seq_box = SequencerBox(
            parent=vert_splitter, mf=self.mf, composition=composition
        )
        vert_splitter.addWidget(tracks_splitter)
        vert_splitter.addWidget(seq_box)
        vert_splitter.track_list = self.map[composition.name]
        self.tab_box.addTab(
            vert_splitter, QIcon(":/icons/composition.png"), composition.name
        )

    def index_of_track_list(self, track_list: TrackList) -> int:
        for index in range(self.tab_box.count()):
            widget = self.tab_box.widget(index)
            if widget.track_list == track_list:
                return index
        return -1

    def delete_composition(self, composition: Composition):
        track_list = self.map.pop(composition.name)
        index = self.index_of_track_list(track_list=track_list)
        for track_name in list(track_list.map.keys()):
            track_list.delete_track(
                composition=composition, track=track_list[track_name].track
            )
        self.tab_box.removeTab(index)
        self.project.delete_composition(composition=composition)
        track_list.deleteLater()
        # self.tab_box.widget(index).deleteLater()

    def delete_all_compositions(self):
        for composition in list(self.project.compositions):
            self.delete_composition(composition=composition)

    @property
    def current_track_list(self) -> TrackList:
        vert_splitter: QSplitter = self.tab_box.currentWidget()
        tracks_splitter: QSplitter = vert_splitter.widget(0)
        track_list: TrackList = tracks_splitter.widget(0)
        if not track_list:
            raise ValueError(f"Cannot determine track list in current composition")
        return track_list

    def init_fonts(self):
        for composition in self:
            for track in self[composition]:
                for track_version in self[composition][track].version_tab:
                    self[composition][track].version_tab[
                        track_version
                    ].track_item.init_fonts()

    def set_keyboard_position(self):
        for composition in self:
            for track in self[composition]:
                for track_version in self[composition][track].version_tab:
                    self[composition][track].version_tab[
                        track_version
                    ].track_item.set_keyboard_position()

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
        else:
            return track_list

    def __len__(self):
        return len(self.map)


class SequencerBox(QWidget):
    def __init__(self, mf, parent, composition: Composition):
        super().__init__(parent=parent)
        self.composition = composition
        self.splitter = QSplitter(Qt.Horizontal)
        self.custom_loop_box = CustomLoopBox(
            parent=self.splitter, mf=mf, composition=composition
        )
        self.splitter.addWidget(self.custom_loop_box)
        self.composition_loop_box = CompositionLoopBox(
            parent=self.splitter, mf=mf, composition=composition
        )
        self.splitter.addWidget(self.composition_loop_box)
        self.main_box = Box(direction=QBoxLayout.TopToBottom)
        # self.main_box.setContentsMargins(5, 5, 5, 5)
        self.main_box.setSpacing(5)
        self.main_box.addWidget(self.splitter)
        self.setLayout(self.main_box)
        self.resize(QSize(self.width(), 400))
        self.register_listeners()

    def register_listeners(self):
        if not pub.subscribe(self.reload_tracks, GuiAttr.REFRESH_LOOPS):
            raise Exception(f"Cannot register listener {GuiAttr.REFRESH_LOOPS}")

    def reload_tracks(self, composition: Composition):
        if self.composition == composition:
            self.custom_loop_box.custom_loop_grid.load_loops()
            self.composition_loop_box.composition_loop_grid.load_loops()


class CustomLoopBox(QWidget):
    def __init__(self, mf, parent, composition: Composition):
        super().__init__(parent=parent)
        self.main_box = Box(direction=QBoxLayout.LeftToRight)
        self.custom_loop_grid = CustomLoopGrid(
            parent=self, mf=mf, composition=composition
        )
        self.main_box.addWidget(self.custom_loop_grid, stretch=1)
        self.setLayout(self.main_box)


class CompositionLoopBox(QWidget):
    def __init__(self, mf, parent, composition: Composition):
        super().__init__(parent=parent)
        self.main_box = Box(direction=QBoxLayout.TopToBottom)
        self.composition_loop_grid = CompositionLoopGrid(
            parent=self, mf=mf, composition=composition
        )
        self.main_box.addWidget(self.composition_loop_grid)
        self.setLayout(self.main_box)
