from __future__ import annotations

import logging
from abc import ABC, abstractmethod
from pathlib import Path
from typing import List, Dict, Tuple, TYPE_CHECKING, Optional
from uuid import UUID

from PySide6.QtCore import Qt
from PySide6.QtGui import QIcon
from PySide6.QtWidgets import (
    QWidget,
    QBoxLayout,
    QComboBox,
    QLabel,
    QTabWidget,
    QMenu,
    QToolButton,
    QTableWidget,
    QTableWidgetItem,
    QButtonGroup,
)
from src.app.gui.editor.piano_roll import PianoRoll
from src.app.model.project_version import ProjectVersion
from src.app.utils.logger import get_console_logger
from src.app.utils.notification import register_listener, notify
from src.app.utils.properties import MenuAttr, NotificationMessage
from src.app.gui.widgets import Box, FontBox, PresetBox, ChannelBox
from src.app.backend.midway_synth import MidwaySynth
from src.app.model.types import Preset, ABCWidgetFinalMeta, Id, NoteUnit
from src.app.model.sequence import Sequence
from src.app.model.track import Track, TrackVersion

if TYPE_CHECKING:
    from src.app.gui.track_list import TrackListItem
    from src.app.gui.main_frame import MainFrame

logger = get_console_logger(name=__name__, log_level=logging.ERROR)


class TrackVersionControlTab(QWidget, ABC, metaclass=ABCWidgetFinalMeta):
    @abstractmethod
    def play(self):
        pass

    @abstractmethod
    def repeat(self) -> bool:
        pass

    @abstractmethod
    def create_piano_roll(self) -> PianoRoll:
        pass


class BaseTrackVersionControlTab(TrackVersionControlTab):
    def __init__(
        self,
        mf: MainFrame,
        parent,
        project_version: ProjectVersion,
        track: Track,
        track_version: TrackVersion,
    ):
        super().__init__(parent=parent)
        self.mf = mf
        self.project_version = project_version
        self.track = track
        self.track_version = track_version
        self.piano_roll = self.create_piano_roll()

        self._font = FontBox(synth=self.synth)
        self.populate_font_combo()
        self._preset = PresetBox(synth=self.synth)
        self._channel = ChannelBox(default_channel=self.channel)

        self.w_play = QToolButton()
        self.w_play.setDefaultAction(self.mf.menu.actions[MenuAttr.TRACK_VERSION_PLAY])
        self.w_stop = QToolButton()
        self.w_stop.setDefaultAction(self.mf.menu.actions[MenuAttr.TRACK_VERSION_STOP])
        # self.w_metronome = QCheckBox("Metronome")
        self.w_stop_all_notes = QToolButton()
        self.w_stop_all_notes.setDefaultAction(self.mf.menu.actions[MenuAttr.TRACK_VERSION_STOP_ALL_NOTES])
        self.config_dlg_btn = QToolButton()
        self.config_dlg_btn.setDefaultAction(self.mf.menu.actions[MenuAttr.TRACK_VERSION_EDIT])
        self.note_length_group = QButtonGroup()
        self.set_note_length_group()

        # Layout
        self.midi_box = Box(direction=QBoxLayout.LeftToRight)
        self.midi_box.setSpacing(5)
        self.midi_box.setContentsMargins(5, 5, 5, 5)
        self.midi_box.addWidget(QLabel("Font"))
        self.midi_box.addWidget(self._font)
        self.midi_box.addWidget(QLabel("Preset"))
        self.midi_box.addWidget(self._preset)
        self.midi_box.addWidget(self._channel)

        self.midi_box.addStretch()

        for button in self.note_length_group.buttons():
            self.midi_box.addWidget(button)
        self.midi_box.addWidget(self.w_play)
        self.midi_box.addWidget(self.w_stop)
        # self.midi_box.addWidget(self.w_metronome)
        self.midi_box.addWidget(self.w_stop_all_notes)
        self.midi_box.addWidget(self.config_dlg_btn)

        self.top_box = Box(direction=QBoxLayout.TopToBottom)
        self.top_box.addLayout(self.midi_box)
        self.main_box = Box(direction=QBoxLayout.TopToBottom)
        self.main_box.addLayout(self.top_box)
        self.main_box.addWidget(self.piano_roll)
        self.setMinimumWidth(500)
        self.setLayout(self.main_box)

        self.num_of_bars = self.track_version.num_of_bars()

        if self.mf.synth.is_loaded():
            self.init_fonts()

    def set_note_length_group(self):
        def on_toggle(checked: bool):
            if checked:
                length = self.note_length_group.id(self.note_length_group.checkedButton())
                self.track_version.note_length = float(length)

        note_length_options = [
            int(NoteUnit.WHOLE),
            int(NoteUnit.HALF),
            int(NoteUnit.QUARTER),
            int(NoteUnit.EIGHTH),
            int(NoteUnit.SIXTEENTH),
            int(NoteUnit.THIRTY_SECOND),
        ]
        for option in note_length_options:
            button = QToolButton()
            button.setCheckable(True)
            button.setText(str(option))
            button.toggled.connect(on_toggle)
            self.note_length_group.addButton(button, option)

        self.note_length_group.button(int(self.track_version.note_length)).setChecked(True)

    def play(self):
        pass

    def create_piano_roll(self) -> Optional[PianoRoll]:
        return None

    def repeat(self) -> bool:
        return True

    def init_fonts(self):
        self.populate_font_combo()
        self._font.currentIndexChanged.connect(self.on_font_change)
        self.sf_name = self.track_version.sf_name
        self._preset.currentIndexChanged.connect(self.on_preset_change)
        self.bank_patch = self.track_version.bank, self.track_version.patch

    def populate_font_combo(self):
        self._font.populate_font_combo()

    def populate_preset_combo(self):
        self._preset.setEditable(False)
        self._preset.setDuplicatesEnabled(False)
        sfid = self.synth.sfid(self.sf_name)
        if self._preset.itemData(0) and self.sf_name == self._preset.itemData(0).sf_name:
            return
        self._preset.populate_preset_combo(sfid=sfid)

    @property
    def synth(self) -> MidwaySynth:
        return self.piano_roll.synth

    @property
    def num_of_bars(self) -> int:
        return self.piano_roll.num_of_bars

    @num_of_bars.setter
    def num_of_bars(self, value: int) -> None:
        self.piano_roll.num_of_bars = value

    def on_font_change(self, index: int):
        self.sf_name = self._font.itemData(index)

    def on_preset_change(self, index: int):
        if index >= 0:
            preset = self._preset.itemData(index)
            self.bank_patch = preset.bank, preset.patch
            logger.debug(f"Preset changed to {preset.bank} {preset.patch}")

    @property
    def channel(self) -> int:
        return self.track_version.channel

    @channel.setter
    def channel(self, value) -> None:
        self.track_version.channel = value
        self.piano_roll.channel = value
        self._channel.setCurrentIndex(value)

    @property
    def sf_name(self) -> str:
        return self.piano_roll.sf_name

    @sf_name.setter
    def sf_name(self, value):
        self.piano_roll.sf_name = value
        index = self._font.findData(value)
        self._font.setCurrentIndex(index)
        self.populate_preset_combo()

    @property
    def sfid(self) -> int:
        return self.synth.sfid(self.sf_name)

    @property
    def preset(self) -> Preset:
        sf_name = self.synth.sf_name(sfid=self.sfid)
        return Preset(
            sf_name=sf_name,
            bank=self.track_version.bank,
            patch=self.track_version.patch,
        )

    @preset.setter
    def preset(self, preset: Preset) -> None:
        self.track_version.sf_name = self.sf_name
        self.track_version.bank = preset.bank
        self.track_version.patch = preset.patch
        self.synth.preset_change(channel=self.channel, preset=preset)
        logger.debug(f"Preset changed {self.track_version.bank}")

    @staticmethod
    def find_preset(cmb: QComboBox, preset: Preset) -> int:
        found = -1
        for index in range(cmb.count()):
            if list(cmb.itemData(index)) == list(preset):
                found = index
                break
        if found == -1:
            raise ValueError(f"Cannot find preset {preset} in combo box")
        return found

    @property
    def bank_patch(self):
        return self.piano_roll.bank_patch

    @bank_patch.setter
    def bank_patch(self, value: Tuple[int, int]):
        sfid = self.synth.sfid(self.sf_name)
        bank, patch = value
        patch_name = self.synth.sfpreset_name(sfid, bank, patch)
        self.preset = Preset(sf_name=self.sf_name, bank=bank, patch=patch)
        index = self.find_preset(cmb=self._preset, preset=self.preset)
        self._preset.setCurrentIndex(index)
        self.mf.show_message(message=f"Soundfont {Path(self.sf_name).name} bank {bank} patch {patch_name}")

    @property
    def sequence(self) -> Sequence:
        return self.piano_roll.sequence

    @sequence.setter
    def sequence(self, value) -> None:
        self.piano_roll.sequence = value

    @property
    def version_name(self) -> str:
        return self.track_version.name

    @version_name.setter
    def version_name(self, name: str) -> None:
        self.track_version.name = name

    def set_keyboard_position(self):
        piano_keyboard = self.piano_roll.grid_view.keyboard_view
        self.piano_roll.grid_view.keyboard_view.verticalScrollBar().setValue(
            piano_keyboard.verticalScrollBar().maximum() // 2
        )


class MelodyTrackVersion(BaseTrackVersionControlTab):
    """
    Widgets contains melody track version controls:
    piano roll, sound font, bank and patch
    """

    def create_piano_roll(self) -> PianoRoll:
        return PianoRoll(
            mf=self.mf,
            parent=self,
            track_version=self.track_version,
            synth=self.mf.synth,
            project_version=self.project_version,
            track=self.track,
        )


class DrumsTrackVersion(QWidget):
    """Widgets contains drums track version controls"""

    def __init__(
        self,
        mf: MainFrame,
        parent,
        track_version: TrackVersion,
        # synth: MidwaySynth,
        project_version: ProjectVersion,
        track: Track,
    ):
        super().__init__(parent=parent)
        self.mf = mf
        self.project_version = project_version
        self.track = track
        self.track_version = track_version


class TrackVersionMidiEvents(QWidget):
    """Widgets contains list of track version events"""

    HEADERS = ["Beat", "Pitch", "Unit", "Velocity", "Preset", "Control"]

    def __init__(
        self,
        mf: MainFrame,
        parent,
        track_version: TrackVersion,
        # synth: MidwaySynth,
        project_version: ProjectVersion,
        track: Track,
    ):
        super().__init__(parent=parent)
        self.mf = mf
        self.project_version = project_version
        self.track = track
        self.track_version = track_version
        self.table = QTableWidget()
        self.table.setColumnCount(len(TrackVersionMidiEvents.HEADERS))
        for index, header in enumerate(TrackVersionMidiEvents.HEADERS):
            item = QTableWidgetItem(header)
            self.table.setHorizontalHeaderItem(index, item)
        self.main_box = Box(direction=QBoxLayout.TopToBottom)
        self.main_box.addWidget(self.table)
        self.setLayout(self.main_box)

    def load_events(self):
        pass


class TrackVersionDetailControl(QWidget):
    """This tab control contains tab with piano roll and track version info"""

    def __init__(
        self,
        mf,
        parent,
        track_version: TrackVersion,
        project_version: ProjectVersion,
        track: Track,
    ):
        super().__init__(parent=parent)
        self.project_version = project_version
        self.track = track
        self.track_version = track_version
        self.tab_box = QTabWidget()
        self.tab_box.setTabPosition(QTabWidget.South)
        self.track_version_control_tab = MelodyTrackVersion(
            mf=mf,
            parent=self,
            track_version=track_version,
            project_version=project_version,
            track=self.track,
        )
        self.tab_box.addTab(self.track_version_control_tab, QIcon(":/icons/piano.png"), "Piano roll")
        self.track_version_table = TrackVersionMidiEvents(
            mf=mf,
            parent=self,
            track_version=track_version,
            # synth=synth,
            project_version=project_version,
            track=self.track,
        )
        self.tab_box.addTab(self.track_version_table, "Events")
        self.main_box = Box(direction=QBoxLayout.TopToBottom)
        self.main_box.addWidget(self.tab_box)
        self.setLayout(self.main_box)


class TrackVersionControl(QWidget):
    """Control tab of track versions"""

    def __init__(
        self,
        mf: MainFrame,
        list_item: TrackListItem,
        track: Track,
        synth: MidwaySynth,
        project_version: ProjectVersion,
    ):
        super().__init__(parent=list_item)
        self.mf = mf
        self.synth = synth
        self.project_version = project_version
        self.track = track
        self.list_item = list_item
        self.tab_box = QTabWidget()
        self.map: Dict[UUID, TrackVersionDetailControl] = {}
        # self.tab_box.setTabsClosable(True)
        for track_version in self.track.versions:
            self._new_track_version(track_version=track_version)
        self.main_box = Box(direction=QBoxLayout.TopToBottom)
        self.main_box.addWidget(self.tab_box)
        self.setLayout(self.main_box)

        self.tab_box.tabBar().setContextMenuPolicy(Qt.CustomContextMenu)
        self.tab_box.tabBar().customContextMenuRequested.connect(self.open_menu)
        self.tab_box.tabBarDoubleClicked.connect(self.on_double_click)
        self.tab_box.tabBarClicked.connect(self.on_click)
        # self.tab_box.currentChanged.connect(self.on_tab_changed)

        register_listener(
            mapping={
                NotificationMessage.TRACK_VERSION_ADDED: self.new_track_version,
                NotificationMessage.TRACK_VERSION_CHANGED: self.change_track_version,
                NotificationMessage.TRACK_VERSION_REMOVED: self.delete_track_version,
            }
        )

    def _new_track_version(self, track_version: TrackVersion):
        logger.debug(f"Added version {track_version}")
        self.map[track_version.id] = TrackVersionDetailControl(
            mf=self.mf,
            parent=self,
            track_version=track_version,
            project_version=self.project_version,
            track=self.track,
        )
        self.tab_box.addTab(
            self.map[track_version.id],
            QIcon(":/icons/note.png"),
            track_version.name,
        )

    def new_track_version(self, track: Track, track_version: TrackVersion):
        if self.track == track:
            self._new_track_version(track_version=track_version)

    def change_track_version(
        self, project_version: ProjectVersion, track_id: Id, track_version_id: Id, new_track_version: TrackVersion
    ):
        if self.project_version == project_version and self.track.id == track_id:
            track_version = self.track.get_version(identifier=track_version_id)
            self.tab_box.setTabText(self.track_version_tab_id(track_version=track_version), new_track_version.name)
            tab = self.track_version_control_tab(track_version=track_version)
            tab.channel = new_track_version.channel
            tab.sf_name = new_track_version.sf_name
            tab.bank_patch = new_track_version.bank, new_track_version.patch

    def _delete_track_version(self, track_version: TrackVersion):
        track_tab = self.map.pop(track_version.id)
        if (index := self.tab_box.indexOf(track_tab)) < 0:
            raise ValueError(f"Cannot find {track_tab.track_version.name} tab when deleting")
        self.tab_box.removeTab(index)
        track_tab.deleteLater()

    def delete_track_version(self, track: Track, track_version: TrackVersion):
        if self.track == track:
            self._delete_track_version(track_version=track_version)

    def on_double_click(self, _):
        self.mf.menu.actions[MenuAttr.TRACK_VERSION_EDIT].trigger()

    def on_click(self, index):
        if 0 <= index < self.tab_box.tabBar().count():
            self.tab_box.setCurrentIndex(index)

    @property
    def versions(self) -> List[str]:
        return [track_version.name for track_version in self.track.versions]

    def __iter__(self):
        return iter(self.map)

    def __getitem__(self, version: UUID) -> TrackVersionDetailControl:
        track_version = self.map.get(version)
        if track_version is None:
            raise IndexError
        return track_version

    def __len__(self):
        return len(self.map)

    def open_menu(self, position):
        menu = QMenu()
        menu.addAction(self.mf.menu.actions[MenuAttr.TRACK_VERSION_NEW])
        menu.addAction(self.mf.menu.actions[MenuAttr.TRACK_VERSION_EDIT])
        menu.addAction(self.mf.menu.actions[MenuAttr.TRACK_VERSION_REMOVE])
        menu.setDefaultAction(self.mf.menu.actions[MenuAttr.TRACK_VERSION_EDIT])
        menu.exec_(self.tab_box.tabBar().mapToGlobal(position))
        # menu.exec_(e.globalPos())

    def track_version_detail_control(self, track_version: TrackVersion) -> TrackVersionDetailControl:
        return self.map[track_version.id]

    def track_version_tab_id(self, track_version: TrackVersion) -> int:
        return self.tab_box.indexOf(self.track_version_detail_control(track_version=track_version))

    def track_version_control_tab(self, track_version: TrackVersion) -> BaseTrackVersionControlTab:
        return self.track_version_detail_control(track_version=track_version).track_version_control_tab

    @property
    def current_track_version_detail_control(self) -> TrackVersionDetailControl:
        return self.tab_box.currentWidget()

    @property
    def current_track_version_control_tab(self) -> BaseTrackVersionControlTab:
        return self.current_track_version_detail_control.track_version_control_tab

    @property
    def current_track_version(self) -> TrackVersion:
        track_tab = self.current_track_version_detail_control
        if not track_tab:
            raise ValueError(f"Cannot determine tab with current track version. Track {self.track.name}")
        return track_tab.track_version

    @current_track_version.setter
    def current_track_version(self, track_version: TrackVersion) -> None:
        if self.tab_box.currentWidget() != self.map[track_version.id]:
            self.tab_box.setCurrentWidget(self.map[track_version.id])

    # def on_tab_changed(self, index: int):
    #     self.select_current_version(current_version=self.tab_box.widget(index).version_name)
    #
    # def select_current_version(self, current_version: str):
    #     if self.tab_box.currentWidget() != self.map[current_version]:
    #         self.tab_box.setCurrentWidget(self.map[current_version])
