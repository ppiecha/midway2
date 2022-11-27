from __future__ import annotations

import logging
from functools import partial
from typing import TYPE_CHECKING, Dict, Callable

from PySide6.QtCore import Qt
from PySide6.QtGui import QAction, QIcon, QKeySequence
from PySide6.QtWidgets import QMenuBar, QMenu, QMessageBox

from src.app.gui.dialogs.generic_config import GenericConfig, GenericConfigMode
from src.app.utils.logger import get_console_logger
from src.app.utils.properties import MenuAttr
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


def map_config(mf: MainFrame) -> Callable:
    project_info = mf.get_current_project_version_info()
    return partial(GenericConfig, mf=mf, project=project_info.project, project_version=project_info.project_version)


# Project


def new_project(_: MainFrame):
    pass


def save_project(_: MainFrame):
    pass


def save_project_as(_: MainFrame):
    pass


def delete_project(mf: MainFrame):
    mf.project_control.delete_all_project_versions()


# Composition


def add_composition(_: MainFrame):
    pass


def rename_composition(_: MainFrame):
    pass


def delete_composition(_: MainFrame):
    pass


# Track


def new_track(mf: MainFrame):
    track_list = mf.project_control.current_track_list
    project_version = track_list.project_version
    if project_version.get_next_free_channel() is not None:
        # config = GenericConfig(mf=mf, mode=GenericConfigMode.NEW_TRACK, project_version=project_version)
        mf.show_config_dlg(config=map_config(mf)(mode=GenericConfigMode.NEW_TRACK, project_version=project_version))
    else:
        mf.show_message_box("Cannot add new track. All channels are already reserved")


def edit_track(mf: MainFrame):
    current_project_version_info = mf.get_current_project_version_info()
    if current_project_version_info.track_list_item:
        current_project_version_info.track_list.edit_track(current_project_version_info.track_list_item.list_item)
    else:
        raise ValueError(
            f"Cannot determine current track in track list in project version "
            f"{current_project_version_info.project_version.name}"
        )


def delete_track(mf: MainFrame):
    current_project_version_info = mf.get_current_project_version_info()
    current_project_version_info.project_version.remove_track(track=current_project_version_info.track)


# Track version


def new_track_version(mf: MainFrame):
    current_project_version = mf.current_project_version
    if current_project_version.get_next_free_channel() is not None:
        mf.show_config_dlg(config=map_config(mf)(mode=GenericConfigMode.NEW_TRACK_VERSION, track=mf.current_track))
    else:
        mf.show_message_box("Cannot add new track. All channels are already reserved")


def edit_track_version(mf: MainFrame):
    mf.show_config_dlg(
        config=map_config(mf)(
            mode=GenericConfigMode.EDIT_TRACK_VERSION, track=mf.current_track, track_version=mf.current_track_version
        )
    )


def delete_track_version(mf: MainFrame):
    current_project_version_info = mf.get_current_project_version_info()
    resp = QMessageBox.question(
        mf,
        "",
        f"This will delete version: {current_project_version_info.track_version.name}<br><b>Are you sure?</b>",
        QMessageBox.Yes | QMessageBox.Cancel,
        QMessageBox.Cancel,
    )
    if resp == QMessageBox.Yes:
        mf.current_project_version.remove_track_version(
            track=current_project_version_info.track, track_version=current_project_version_info.track_version
        )


def play_track_version(mf: MainFrame):
    current_project_version_info = mf.get_current_project_version_info()
    mf.synth.play_track_version(
        track=current_project_version_info.track,
        track_version=current_project_version_info.track_version,
        bpm=current_project_version_info.project_version.bpm,
        repeat=current_project_version_info.track_version_control_tab.repeat(),
    )


def stop_track_version(mf: MainFrame):
    mf.synth.stop()


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
        MenuAttr.TRACK_REMOVE: Action(
            mf=mf,
            caption=MenuAttr.TRACK_REMOVE,
            slot=delete_track,
            icon=QIcon(":/icons/delete.png"),
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
        MenuAttr.TRACK_VERSION_REMOVE: Action(
            mf=mf,
            caption=MenuAttr.TRACK_VERSION_REMOVE,
            slot=delete_track_version,
            icon=QIcon(":/icons/delete.png"),
            shortcut=QKeySequence(Qt.Key_Delete),
        ),
        MenuAttr.TRACK_VERSION_PLAY: Action(
            mf=mf,
            caption=MenuAttr.TRACK_VERSION_PLAY,
            slot=play_track_version,
            icon=QIcon(":/icons/play.png"),
        ),
        MenuAttr.TRACK_VERSION_STOP: Action(
            mf=mf,
            caption=MenuAttr.TRACK_VERSION_STOP,
            slot=stop_track_version,
            icon=QIcon(":/icons/stop.png"),
        ),
        MenuAttr.TRACK_VERSION_STOP_ALL_NOTES: Action(
            mf=mf,
            caption=MenuAttr.TRACK_VERSION_STOP_ALL_NOTES,
            slot=None,
            icon=QIcon(":/icons/stop_all.png"),
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
