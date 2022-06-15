from __future__ import annotations

import logging
from functools import partial
from typing import TYPE_CHECKING, Dict

from PySide6.QtCore import Qt
from PySide6.QtGui import QAction, QIcon, QKeySequence
from PySide6.QtWidgets import QMenuBar, QMenu
from pubsub import pub

from src.app.gui.dialogs.generic_config import GenericConfig, GenericConfigMode
from src.app.model.composition import Composition
from src.app.model.track import Track
from src.app.utils.logger import get_console_logger
from src.app.utils.properties import GuiAttr, MenuAttr
import src.app.resources  # pylint: disable=unused-import

if TYPE_CHECKING:
    from src.app.gui.main_frame import MainFrame

logger = get_console_logger(name=__name__, log_level=logging.DEBUG)


class Action(QAction):
    def __init__(
        self,
        mf: MainFrame,
        caption: str = None,
        icon: QIcon = None,
        shortcut=None,
        slot=None,
        tip=None,
        status_tip=None,
    ):
        super().__init__(caption, mf)
        if icon:
            self.setIcon(icon)
        if shortcut:
            self.setShortcut(shortcut)
        self.setToolTip(tip or caption)
        self.setStatusTip(status_tip or caption)
        if slot:
            self.triggered.connect(partial(slot, mf=mf))
        mf.addAction(self)


# Project


def new_project(_: MainFrame):
    pass


def save_project(_: MainFrame):
    pass


def save_project_as(_: MainFrame):
    pass


def delete_project(mf: MainFrame):
    mf.composition_tab.delete_all_compositions()


# Composition


def add_composition(_: MainFrame):
    pass


def rename_composition(_: MainFrame):
    pass


def delete_composition(_: MainFrame):
    pass


# Track


def new_track(mf: MainFrame):
    track_list = mf.composition_tab.current_track_list
    project_version = track_list.project_version
    if project_version.get_next_free_channel() is not None:
        config = GenericConfig(mf=mf, mode=GenericConfigMode.new_track, project_version=project_version)
        mf.show_config_dlg(config=config)
    else:
        mf.show_message_box("Cannot add new track. All channels are already reserved")


def edit_track(mf: MainFrame):
    track_list = mf.composition_tab.current_track_list
    if track_list.currentItem():
        track_list.edit_track(track_list.currentItem())
    else:
        raise ValueError(
            f"Cannot determine current track in track list in composition {track_list.project_version_box}"
        )


def delete_track(_: MainFrame):
    pass


# Track version


def new_track_version(mf: MainFrame):
    track_list = mf.composition_tab.current_track_list
    composition = track_list.project_version_box
    track = track_list.current_track_list_item.track_box
    if composition.get_next_free_channel() is not None:
        config = GenericConfig(
            mf=mf,
            mode=GenericConfigMode.new_track_version,
            composition=composition,
            track=track,
        )
        mf.show_config_dlg(config=config)
    else:
        mf.show_message_box("Cannot add new track. All channels are already reserved")


def edit_track_version(mf: MainFrame):
    track_list = mf.composition_tab.current_track_list
    project_version = track_list.project_version
    track = track_list.current_track_list_item.track
    track_version = track_list.current_track_list_item.current_track_version
    config = GenericConfig(
        mf=mf,
        mode=GenericConfigMode.edit_track_version,
        project_version=project_version,
        track=track,
        track_version=track_version,
    )
    mf.show_config_dlg(config=config)


def delete_track_version(_: MainFrame):
    pass


def play_track_version(_: MainFrame):
    pass


def get_actions(mf: MainFrame) -> Dict[str, Action]:
    return {
        MenuAttr.PROJECT_NEW: Action(mf=mf, caption=MenuAttr.PROJECT_NEW, slot=new_project),
        MenuAttr.TRACK_NEW: Action(
            mf=mf,
            caption=MenuAttr.TRACK_NEW,
            slot=new_track,
            icon=QIcon(":/icons/add.png"),
            shortcut=QKeySequence(Qt.CTRL | Qt.Key_T),
        ),
        MenuAttr.TRACK_EDIT: Action(
            mf=mf,
            caption=MenuAttr.TRACK_EDIT,
            slot=edit_track,
            icon=QIcon(":/icons/edit.png"),
        ),
        MenuAttr.TRACK_VERSION_NEW: Action(
            mf=mf,
            caption=MenuAttr.TRACK_VERSION_NEW,
            slot=new_track_version,
            icon=QIcon(":/icons/add.png"),
            shortcut=QKeySequence(Qt.CTRL | Qt.Key_N),
        ),
        MenuAttr.TRACK_VERSION_EDIT: Action(
            mf=mf,
            caption=MenuAttr.TRACK_VERSION_EDIT,
            slot=edit_track_version,
            icon=QIcon(":/icons/edit.png"),
        ),
        MenuAttr.TRACK_VERSION_PLAY: Action(
            mf=mf,
            caption=MenuAttr.TRACK_VERSION_PLAY,
            slot=play_track_version,
            icon=QIcon(":/icons/play.png"),
        ),
    }


class MenuBar(QMenuBar):
    def __init__(self, main_form):
        super().__init__(main_form)
        file_menu = QMenu("&File", self)
        self.addMenu(file_menu)
        self.actions = get_actions(mf=main_form)
        file_menu.addAction(self.actions[MenuAttr.PROJECT_NEW])

    # Notifications

    # @staticmethod
    # def post_new_track(composition: Composition, track: Track):
    #     pub.sendMessage(topicName=GuiAttr.NEW_TRACK, composition=composition, track=track)
    #
    # @staticmethod
    # def post_refresh_loops(composition: Composition):
    #     pub.sendMessage(topicName=GuiAttr.REFRESH_LOOPS, composition=composition)
