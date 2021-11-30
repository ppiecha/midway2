from __future__ import annotations
from functools import partial

from PySide6.QtCore import Qt
from PySide6.QtGui import QAction, QIcon, QKeySequence
from PySide6.QtWidgets import QMenuBar, QMenu

from constants import NEW_PROJECT, NEW_TRACK, NEW_COMPOSITION, \
    NEW_TRACK_VERSION, EDIT_TRACK_VERSION, EDIT_TRACK, \
    DELETE_PROJECT, REFRESH_LOOPS

from typing import TYPE_CHECKING, Dict

from gui.dialogs.generic_config import GenericConfig, GenericConfigMode

from pubsub import pub

import resources
from model.composition import Composition
from model.track import Track

if TYPE_CHECKING:
    from gui.main_frame import MainFrame


class Action(QAction):
    def __init__(self, mf: MainFrame, caption: str = None, icon: QIcon = None,
                 shortcut=None, slot=None, tip=None,
                 status_tip=None):
        super().__init__(caption, mf)
        if icon:
            self.setIcon(icon)
        if shortcut:
            self.setShortcut(shortcut)
        self.setToolTip(tip or caption)
        self.setStatusTip(status_tip or caption)
        if slot:
            self.triggered.connect(partial(slot, mf=mf))
        # connect(openAct, & QAction::triggered, this, & MainWindow::open);
        mf.addAction(self)


# Project

def new_project(mf: MainFrame):
    pass


def save_project(mf: MainFrame):
    pass


def save_project_as(mf: MainFrame):
    pass


def delete_project(mf: MainFrame):
    mf.composition_tab.delete_all_compositions()


# Composition

def add_composition(mf: MainFrame):
    pass


def rename_composition(mf: MainFrame):
    pass


def delete_composition(mf: MainFrame):
    pass


# Track

def new_track(mf: MainFrame):
    track_list = mf.composition_tab.current_track_list
    composition = track_list.composition
    if composition.get_next_free_channel() is not None:
        config = GenericConfig(mf=mf, mode=GenericConfigMode.new_track,
                               composition=composition)
        mf.show_config_dlg(config=config)
    else:
        mf.show_message_box(
            f'Cannot add new track. All channels are already reserved')


def edit_track(mf: MainFrame):
    track_list = mf.composition_tab.current_track_list
    if track_list.currentItem():
        track_list.edit_track(track_list.currentItem())
    else:
        raise ValueError(
            f'Cannot determine current track in track list in composition {track_list.composition_box}')


def delete_track(mf: MainFrame):
    pass


# Track version

def new_track_version(mf: MainFrame):
    track_list = mf.composition_tab.current_track_list
    composition = track_list.composition_box
    track = track_list.current_track_list_item.track_box
    if composition.get_next_free_channel() is not None:
        config = GenericConfig(mf=mf, mode=GenericConfigMode.new_track_version,
                               composition=composition, track=track)
        mf.show_config_dlg(config=config)
    else:
        mf.show_message_box(
            f'Cannot add new track. All channels are already reserved')


def edit_track_version(mf: MainFrame):
    track_list = mf.composition_tab.current_track_list
    composition = track_list.composition
    track = track_list.current_track_list_item.track
    track_version = track_list.current_track_list_item.current_track_version
    config = GenericConfig(mf=mf, mode=GenericConfigMode.edit_track_version,
                           composition=composition, track=track,
                           track_version=track_version)
    mf.show_config_dlg(config=config)


def delete_track_version(mf: MainFrame):
    pass


# Custom loop

def add_custom_loop(mf: MainFrame):
    pass


def edit_custom_loop(mf: MainFrame):
    pass


def delete_custom_loop(mf: MainFrame):
    pass


def get_actions(mf: MainFrame) -> Dict[str, Action]:
    return {
        NEW_PROJECT: Action(mf=mf, caption=NEW_PROJECT, slot=new_project),
        DELETE_PROJECT: Action(mf=mf, caption=DELETE_PROJECT,
                               slot=delete_project),
        NEW_COMPOSITION: Action(mf=mf, caption=NEW_COMPOSITION, slot=None),
        NEW_TRACK: Action(mf=mf, caption=NEW_TRACK, slot=new_track,
                          icon=QIcon(":/icons/add.png"),
                          shortcut=QKeySequence(Qt.CTRL | Qt.Key_T)),
        EDIT_TRACK: Action(mf=mf, caption=EDIT_TRACK, slot=edit_track,
                           icon=QIcon(":/icons/edit.png")),
        NEW_TRACK_VERSION: Action(mf=mf, caption=NEW_TRACK_VERSION,
                                  slot=new_track_version,
                                  icon=QIcon(":/icons/add.png"),
                                  shortcut=QKeySequence(Qt.CTRL | Qt.Key_N)),
        EDIT_TRACK_VERSION: Action(mf=mf, caption=EDIT_TRACK_VERSION,
                                   slot=edit_track_version,
                                   icon=QIcon(":/icons/edit.png"))
    }


class MenuBar(QMenuBar):
    def __init__(self, main_form):
        super().__init__(main_form)
        file_menu = QMenu("&File", self)
        self.addMenu(file_menu)
        self.actions = get_actions(mf=main_form)
        file_menu.addAction(self.actions[NEW_PROJECT])
        file_menu.addAction(self.actions[DELETE_PROJECT])

    # Notifications

    @staticmethod
    def post_new_track(composition: Composition, track: Track):
        pub.sendMessage(topicName=NEW_TRACK, composition=composition,
                        track=track)

    @staticmethod
    def post_refresh_loops(composition: Composition):
        pub.sendMessage(topicName=REFRESH_LOOPS, composition=composition)
