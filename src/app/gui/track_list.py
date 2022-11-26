"""
Module contains track item and list of track items definition.
It controls adding and deleting tracks in composition
"""

from __future__ import annotations

from typing import Dict
from typing import TYPE_CHECKING
from uuid import UUID

from PySide6.QtCore import QSize
from PySide6.QtGui import QPixmap, Qt
from PySide6.QtWidgets import (
    QWidget,
    QBoxLayout,
    QListWidget,
    QListWidgetItem,
    QLabel,
    QStackedWidget,
    QFrame,
    QToolBar,
)
from pubsub import pub

from src.app.gui.dialogs.generic_config import GenericConfig, GenericConfigMode
from src.app.gui.track_control import TrackVersionControl, BaseTrackVersionControlTab
from src.app.gui.widgets import Box
from src.app.model.composition import Composition
from src.app.model.project_version import ProjectVersion
from src.app.model.track import Track, TrackVersion
from src.app.utils.properties import NotificationMessage, MenuAttr
import src.app.resources  # pylint: disable=unused-import

if TYPE_CHECKING:
    from src.app.gui.main_frame import MainFrame


class TrackListItem(QWidget):
    def __init__(
        self,
        mf: MainFrame,
        parent,
        track: Track,
        list_item: QListWidgetItem,
        project_version: ProjectVersion,
    ):
        super().__init__(parent=parent)
        self.track = track
        self.list_item = list_item
        self.version_tab = TrackVersionControl(
            mf=mf, list_item=self, track=track, synth=mf.synth, project_version=project_version
        )
        self.icon = QLabel()
        self.icon.setPixmap(QPixmap(":/icons/track_item.png"))
        self.name = QLabel(track.name)
        self.main_box = Box(direction=QBoxLayout.LeftToRight)
        self.main_box.setContentsMargins(5, 0, 0, 0)
        self.frame = QFrame(self)
        self.frame.setFrameStyle(QFrame.StyledPanel | QFrame.Raised)
        self.frame.setLayout(self.main_box)
        self.frame_box = Box(direction=QBoxLayout.LeftToRight)
        self.frame_box.addWidget(self.frame)
        self.main_box.addWidget(self.icon)
        self.main_box.setSpacing(5)
        self.main_box.addWidget(self.name)
        self.main_box.addStretch()

        self.setLayout(self.frame_box)

        # self.update_version_list(current_version=current_version)

    @property
    def current_track_version(self) -> TrackVersion:
        return self.version_tab.current_track_version

    @property
    def current_track_version_control_tab(self) -> BaseTrackVersionControlTab:
        return self.version_tab.current_track_version_control_tab

    @current_track_version.setter
    def current_track_version(self, track_version: TrackVersion) -> None:
        self.version_tab.current_track_version = track_version

    # def on_current_changed(self, index):
    #     self.version_tab.select_current_version(current_version=self.w_version.itemText(index))
    #
    # def update_version_list(self, current_version: str):
    #     self.w_version.clear()
    #     self.w_version.addItems(self.version_tab.versions)
    #     self.w_version.setCurrentText(current_version)
    #
    # @property
    # def current_version(self) -> str:
    #     return self.w_version.currentText()
    #
    # @current_version.setter
    # def current_version(self, value: str) -> None:
    #     if self.w_version.currentText() != value:
    #         self.w_version.setCurrentText(value)
    #     self.version_tab.current_version = value


class TrackList(QListWidget):
    def __init__(self, mf: MainFrame, parent, stack: QStackedWidget, project_version: ProjectVersion):
        super().__init__(parent=parent)
        self.mf = mf
        self.project_version = project_version
        self.list = QListWidget(self)
        self.map: Dict[UUID, TrackListItem] = {}
        self.stack = stack
        for track in project_version.tracks:
            self._new_track(track=track)
        self.select_first_item()
        self.main_box = Box(direction=QBoxLayout.TopToBottom)
        self.toolbar = TrackListToolbar(mf=mf, track_list=self)
        self.main_box.addWidget(self.toolbar)
        self.main_box.addWidget(self.list)
        self.setLayout(self.main_box)

        self.list.currentRowChanged.connect(self.display)
        self.list.itemActivated.connect(self.edit_track)

        self.register_listeners()

    @property
    def current_track_list_item(self) -> TrackListItem:
        current_item = self.list.currentItem()
        if not current_item:
            raise ValueError(f"Cannot determine current item in track list in composition {self.project_version}")
        return self.list.itemWidget(current_item)

    def select_first_item(self):
        if self.list.count():
            self.list.setCurrentRow(0)

    def _new_track(self, track: Track):
        widget_item = QListWidgetItem(self.list)
        self.map[track.id] = TrackListItem(
            mf=self.mf,
            parent=self,
            track=track,
            list_item=widget_item,
            project_version=self.project_version,
        )
        self.stack.addWidget(self.map[track.id].version_tab)
        widget_item.setSizeHint(self.map[track.id].sizeHint())
        self.list.addItem(widget_item)
        self.list.setItemWidget(widget_item, self.map[track.id])

    def edit_track(self, item: QListWidgetItem):
        track_list_item: TrackListItem = self.list.itemWidget(item)
        config = GenericConfig(
            mf=self.mf,
            mode=GenericConfigMode.EDIT_TRACK,
            project_version=self.project_version,
            track=track_list_item.track,
        )
        self.mf.show_config_dlg(config=config)

    def _delete_track(self, track: Track):
        if not self.project_version.track_exists(identifier=track.id):
            raise ValueError(f"Track with name {track.id} does not exist in composition {self.project_version.name}")
        track_list_item: TrackListItem = self.map.pop(track.id)
        self.list.removeItemWidget(track_list_item.list_item)
        self.stack.removeWidget(track_list_item)
        for track_version_name in list(track_list_item.version_tab.map.keys()):
            track_list_item.version_tab._delete_track_version(
                track_version=track_list_item.track.get_version(identifier=track_version_name)
            )
        self.project_version.remove_track(track=track)
        track_list_item.deleteLater()

    def register_listeners(self):
        if not pub.subscribe(self.new_track, NotificationMessage.TRACK_ADDED):
            raise Exception(f"Cannot register listener {NotificationMessage.TRACK_ADDED}")
        if not pub.subscribe(self.rename_track, NotificationMessage.TRACK_CHANGED):
            raise Exception(f"Cannot register listener {NotificationMessage.TRACK_CHANGED}")
        if not pub.subscribe(self.delete_track, NotificationMessage.TRACK_REMOVED):
            raise Exception(f"Cannot register listener {NotificationMessage.TRACK_REMOVED}")

    def unregister_listener(self, topic):
        pass

    def new_track(self, project_version: ProjectVersion, track: Track):
        if self.project_version == project_version:
            self._new_track(track=track)
            # self.mf.menu.post_refresh_loops(composition=composition)

    def rename_track(self, composition: Composition, track: Track, new_name: str):
        pass

    def delete_track(self, project_version: ProjectVersion, track: Track):
        if self.project_version == project_version:
            self._delete_track(track=track)

    def display(self, current: int):
        self.stack.setCurrentIndex(current)

    def __iter__(self):
        return iter(self.map)

    def __getitem__(self, track_id: UUID) -> TrackListItem:
        track_list_item = self.map[track_id]
        if track_list_item is None:
            raise IndexError
        return track_list_item

    def __len__(self):
        return len(self.map)


class TrackListToolbar(QToolBar):
    def __init__(self, mf: MainFrame, track_list: TrackList):
        super().__init__("Track list", track_list)
        self.setToolButtonStyle(Qt.ToolButtonIconOnly)
        self.setIconSize(QSize(16, 16))
        self.addAction(mf.menu.actions[MenuAttr.TRACK_NEW])
