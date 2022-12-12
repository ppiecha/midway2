from __future__ import annotations

import logging
from functools import partial
from typing import TYPE_CHECKING, Dict, Callable

from PySide6.QtCore import Qt
from PySide6.QtGui import QIcon, QKeySequence
from PySide6.QtWidgets import QMenuBar, QMenu, QMessageBox

from src.app.gui.dialogs.generic_config import GenericConfig, GenericConfigMode
from src.app.gui.widgets import Action
from src.app.model.project import reset_project, is_project_empty
from src.app.utils.logger import get_console_logger
from src.app.utils.properties import MenuAttr, PlayOptions

if TYPE_CHECKING:
    from src.app.gui.main_frame import MainFrame


logger = get_console_logger(name=__name__, log_level=logging.DEBUG)


def map_config(mf: MainFrame) -> Callable:
    project_info = mf.get_current_project_version_info()
    return partial(GenericConfig, mf=mf, project=project_info.project, project_version=project_info.project_version)


def config_by_mode(mf: MainFrame, config_mode: GenericConfigMode) -> GenericConfig:
    project_info = mf.get_current_project_version_info()
    config_creator = partial(GenericConfig, mf=mf, project=project_info.project)
    match config_mode:
        case GenericConfigMode.NEW_PROJECT | GenericConfigMode.NEW_PROJECT_VERSION as mode:
            config_creator = partial(config_creator, mode=mode)
    return config_creator()


def slot_by_mode(mf: MainFrame, config_mode: GenericConfigMode) -> None:
    config = config_by_mode(mf=mf, config_mode=config_mode)
    match config_mode:
        case GenericConfigMode.NEW_PROJECT:
            if not is_project_empty(project=config.project):
                if mf.action_not_saved_changes() == QMessageBox.Cancel:
                    return
                mf.project = reset_project(project=config.project)
            mf.show_config_dlg(config=config)
        case GenericConfigMode.NEW_PROJECT_VERSION:
            pass


def get_actions(mf: MainFrame) -> Dict[str, Action]:
    return {
        MenuAttr.PROJECT_NEW: Action(
            mf=mf,
            caption=MenuAttr.PROJECT_NEW,
            slot=partial(slot_by_mode, config_mode=GenericConfigMode.NEW_PROJECT),
            icon=None,
            shortcut=None,
        ),
        MenuAttr.PROJECT_SAVE: Action(
            mf=mf,
            caption=MenuAttr.PROJECT_SAVE,
            slot=save_project,
            icon=None,
            shortcut=QKeySequence(Qt.CTRL | Qt.Key_S),
        ),
        MenuAttr.PROJECT_SAVE_AS: Action(
            mf=mf,
            caption=MenuAttr.PROJECT_SAVE_AS,
            slot=save_project_as,
            icon=None,
            shortcut=QKeySequence(Qt.CTRL | Qt.SHIFT | Qt.Key_S),
        ),
        MenuAttr.PROJECT_CLOSE: Action(
            mf=mf,
            caption=MenuAttr.PROJECT_CLOSE,
            slot=partial(slot_by_mode, config_mode=GenericConfigMode.CLOSE_PROJECT),
            icon=None,
            shortcut=None,
        ),
        MenuAttr.PROJECT_VERSION_NEW: Action(
            mf=mf,
            caption=MenuAttr.PROJECT_VERSION_NEW,
            slot=add_project_version,
            icon=None,
            shortcut=QKeySequence(Qt.CTRL | Qt.SHIFT | Qt.Key_N),
        ),
        MenuAttr.PROJECT_OPEN: Action(
            mf=mf,
            caption=MenuAttr.PROJECT_OPEN,
            slot=open_project,
            icon=None,
            shortcut=QKeySequence(Qt.CTRL | Qt.Key_O),
        ),
        MenuAttr.WINDOW_NEW: Action(
            mf=mf,
            caption=MenuAttr.WINDOW_NEW,
            slot=new_window,
            icon=None,
            shortcut=None,
        ),
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
        MenuAttr.SINGLE_VARIANT_NEW: Action(
            mf=mf,
            caption=MenuAttr.SINGLE_VARIANT_NEW,
            slot=add_single_variant,
            icon=QIcon(":/icons/add.png"),
        ),
    }


class MenuBar(QMenuBar):
    def __init__(self, main_form):
        super().__init__(main_form)
        file_menu = QMenu("&File", self)
        self.addMenu(file_menu)
        self.actions = get_actions(mf=main_form)

        # File
        file_menu.addAction(self.actions[MenuAttr.PROJECT_NEW])
        file_menu.addAction(self.actions[MenuAttr.PROJECT_OPEN])
        file_menu.addAction(self.actions[MenuAttr.WINDOW_NEW])
        file_menu.addSeparator()
        file_menu.addAction(self.actions[MenuAttr.PROJECT_SAVE])
        file_menu.addAction(self.actions[MenuAttr.PROJECT_SAVE_AS])
        file_menu.addSeparator()
        file_menu.addAction(self.actions[MenuAttr.PROJECT_CLOSE])

        # Track
        track_menu = QMenu("&Track", self)
        self.addMenu(track_menu)
        track_menu.addAction(self.actions[MenuAttr.TRACK_NEW])


def new_window(_: MainFrame):
    pass


# Project


def new_project(mf: MainFrame):
    mf.show_config_dlg(config=map_config(mf)(mode=GenericConfigMode.NEW_PROJECT_VERSION))


def open_project(_: MainFrame):
    pass


def save_project(_: MainFrame):
    pass


def save_project_as(_: MainFrame):
    pass


# Project version


def add_project_version(_: MainFrame):
    pass


def rename_project_version(_: MainFrame):
    pass


def delete_project_version(_: MainFrame):
    pass


# Track


def new_track(mf: MainFrame):
    track_list = mf.project_control.current_track_list
    project_version = track_list.project_version
    if project_version.get_next_free_channel() is not None:
        mf.show_config_dlg(config=map_config(mf)(mode=GenericConfigMode.NEW_TRACK, project_version=project_version))
    else:
        mf.show_message_box("Cannot add new track. All channels are already reserved")


def edit_track(mf: MainFrame):
    mf.show_config_dlg(config=map_config(mf)(mode=GenericConfigMode.EDIT_TRACK, track=mf.current_track))


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
        options=PlayOptions(
            bpm=current_project_version_info.project_version.bpm,
            repeat=current_project_version_info.track_version_control_tab.repeat(),
        ),
    )


def stop_track_version(mf: MainFrame):
    mf.synth.stop()


# Single variant


def add_single_variant(mf: MainFrame):
    current_project_version_info = mf.get_current_project_version_info()
    current_project_version_info.project_version.add_single_variant(name="test1", selected=True, enable_all_tracks=True)


# TODO play current composition
