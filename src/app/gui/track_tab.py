from __future__ import annotations

import logging
from pathlib import Path
from typing import List, Dict, Tuple, TYPE_CHECKING
from PySide6.QtCore import Qt
from PySide6.QtGui import QIcon
from PySide6.QtWidgets import (
    QWidget,
    QBoxLayout,
    QCheckBox,
    QComboBox,
    QLabel,
    QPushButton,
    QTabWidget,
    QMenu,
    QToolButton,
    QTableWidget,
    QTableWidgetItem,
)
from src.app.gui.editor.piano_roll import PianoRoll
from src.app.utils.logger import get_console_logger
from src.app.utils.properties import GuiAttr
from src.app.gui.widgets import Box, FontBox, PresetBox, ChannelBox
from src.app.backend.midway_synth import MidwaySynth
from src.app.model.composition import Composition
from src.app.model.event import Preset
from src.app.model.sequence import Sequence
from src.app.model.track import Track, TrackVersion

if TYPE_CHECKING:
    from src.app.gui.track_list import TrackListItem
    from src.app.gui.main_frame import MainFrame

logger = get_console_logger(name=__name__, log_level=logging.DEBUG)


class MelodyTrackVersion(QWidget):
    """
    Widgets contains melody track version controls:
    piano roll, sound font, bank and patch
    """

    def __init__(
        self,
        mf: MainFrame,
        parent,
        track_version: TrackVersion,
        synth: MidwaySynth,
        composition: Composition,
        track: Track,
    ):
        super().__init__(parent=parent)
        self.mf = mf
        self.composition = composition
        self.track = track
        self.track_version = track_version
        self.piano_roll = PianoRoll(
            mf=mf,
            parent=self,
            track_version=track_version,
            synth=synth,
            composition=composition,
            track=track,
        )
        self.midi_box = Box(direction=QBoxLayout.LeftToRight)
        self._channel = ChannelBox(default_channel=self.channel)
        self._font = FontBox(synth=self.synth)
        self.populate_font_combo()
        self._preset = PresetBox(synth=self.synth)
        self.config_dlg_btn = QToolButton()
        self.config_dlg_btn.setDefaultAction(self.mf.menu.actions[GuiAttr.EDIT_TRACK_VERSION])
        self.w_play = QToolButton()
        self.w_play.setDefaultAction(self.piano_roll.ac_play)
        self.w_stop = QPushButton("Stop")
        self.w_metronome = QCheckBox("Metronome")
        self.w_stop_all_notes = QPushButton("Stop")
        self.midi_box.setSpacing(5)
        self.midi_box.setContentsMargins(5, 5, 5, 5)
        self.midi_box.addWidget(QLabel("Font"))
        self.midi_box.addWidget(self._font)
        self.midi_box.addWidget(QLabel("Preset"))
        self.midi_box.addWidget(self._preset)
        self.midi_box.addWidget(self.config_dlg_btn)
        self.midi_box.addWidget(self.w_play)
        self.midi_box.addWidget(self.w_stop)
        self.midi_box.addWidget(self.w_metronome)
        self.midi_box.addWidget(self.w_stop_all_notes)
        self.midi_box.addStretch()
        self.midi_box.addWidget(self._channel)
        self.top_box = Box(direction=QBoxLayout.TopToBottom)
        self.top_box.addLayout(self.midi_box)
        self.main_box = Box(direction=QBoxLayout.TopToBottom)
        self.main_box.addLayout(self.top_box)
        self.main_box.addWidget(self.piano_roll)
        self.setMinimumWidth(500)
        self.setLayout(self.main_box)

        self.num_of_bars = self.track_version.num_of_bars()

    def set_keyboard_position(self):
        piano_keyboard = self.piano_roll.grid_view.keyboard_view
        self.piano_roll.grid_view.keyboard_view.verticalScrollBar().setValue(
            piano_keyboard.verticalScrollBar().maximum() // 2
        )

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
        self.track_version.bank = preset.bank
        self.track_version.patch = preset.patch
        self.synth.preset_change(channel=self.channel, preset=preset)

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
        return self.track_version.version_name

    @version_name.setter
    def version_name(self, name: str) -> None:
        self.track_version.version_name = name
        # TODO call list refresh and update tab name


class DrumsTrackVersion(QWidget):
    """Widgets contains drums track version controls"""

    def __init__(
        self,
        mf: MainFrame,
        parent,
        track_version: TrackVersion,
        # synth: MidwaySynth,
        composition: Composition,
        track: Track,
    ):
        super().__init__(parent=parent)
        self.mf = mf
        self.composition = composition
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
        composition: Composition,
        track: Track,
    ):
        super().__init__(parent=parent)
        self.mf = mf
        self.composition = composition
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


class TrackTab(QWidget):
    """This tab control contains tab with piano roll and track version info"""

    def __init__(
        self,
        mf,
        parent,
        track_version: TrackVersion,
        synth: MidwaySynth,
        composition: Composition,
        track: Track,
    ):
        super().__init__(parent=parent)
        self.composition = composition
        self.track = track
        self.track_version = track_version
        self.tab_box = QTabWidget()
        self.tab_box.setTabPosition(QTabWidget.South)
        self.track_item = MelodyTrackVersion(
            mf=mf,
            parent=self,
            track_version=track_version,
            synth=synth,
            composition=composition,
            track=self.track,
        )
        self.tab_box.addTab(self.track_item, QIcon(":/icons/piano.png"), "Piano roll")
        self.track_version_table = TrackVersionMidiEvents(
            mf=mf,
            parent=self,
            track_version=track_version,
            # synth=synth,
            composition=composition,
            track=self.track,
        )
        self.tab_box.addTab(self.track_version_table, "Events")
        self.main_box = Box(direction=QBoxLayout.TopToBottom)
        self.main_box.addWidget(self.tab_box)
        self.setLayout(self.main_box)


class TrackVersionTab(QWidget):
    """Control tab of track versions"""

    def __init__(
        self,
        mf: MainFrame,
        list_item: TrackListItem,
        track: Track,
        synth: MidwaySynth,
        composition: Composition,
    ):
        super().__init__(parent=list_item)
        self.mf = mf
        self.synth = synth
        self.composition = composition
        self.track = track
        self.list_item = list_item
        self.tab_box = QTabWidget()
        self.map: Dict[str, TrackTab] = {}
        # self.tab_box.setTabsClosable(True)
        for track_version in self.track.versions:
            self._new_track_version(track_version=track_version)
        self.main_box = Box(direction=QBoxLayout.TopToBottom)
        self.main_box.addWidget(self.tab_box)
        self.setLayout(self.main_box)

        self.tab_box.tabBar().setContextMenuPolicy(Qt.CustomContextMenu)
        self.tab_box.tabBar().customContextMenuRequested.connect(self.open_menu)
        self.tab_box.tabBarDoubleClicked.connect(self.on_double_click)
        # self.tab_box.currentChanged.connect(self.on_tab_changed)

    def _new_track_version(self, track_version: TrackVersion):
        self.map[track_version.version_name] = TrackTab(
            mf=self.mf,
            parent=self,
            track_version=track_version,
            synth=self.synth,
            composition=self.composition,
            track=self.track,
        )
        self.tab_box.addTab(
            self.map[track_version.version_name],
            QIcon(":/icons/note.png"),
            track_version.version_name,
        )

    def new_track_version(self, track: Track, track_version: TrackVersion):
        if self.track == track:
            self._new_track_version(track_version=track_version)

    def _delete_track_version(self, track_version: TrackVersion):
        self.track.get_version(version_name=track_version.version_name, raise_not_found=True)
        track_tab = self.map.pop(track_version.version_name)
        if (index := self.tab_box.indexOf(track_tab)) < 0:
            raise ValueError(f"Cannot find {track_tab.track_version.version_name} tab when deleting")
        self.tab_box.removeTab(index)
        self.track.delete_track_version(track_version=track_version)
        track_tab.deleteLater()

    def on_double_click(self, _):
        self.mf.menu.actions[GuiAttr.EDIT_TRACK_VERSION].trigger()

    @property
    def versions(self) -> List[str]:
        return [track_version.version_name for track_version in self.track.versions]

    def __iter__(self):
        return iter(self.map)

    def __getitem__(self, version: str) -> TrackTab:
        track_version = self.map.get(version)
        if track_version is None:
            raise IndexError
        return track_version

    def __len__(self):
        return len(self.map)

    # def rename_version(self, old_version: str, new_version: str):
    #     index = self.tab_box.indexOf(self.map[old_version])
    #     self.tab_box.setTabText(index, new_version)
    #     if new_version in self.versions:
    #         raise ValueError(f'Version {new_version} already exists in track {self.track}')
    #     else:
    #         self.map[new_version] = self.map[old_version]
    #         self.map.pop(old_version)
    #         self.track.versions[new_version] = self.track.versions[old_version]
    #         self.track.versions.pop(old_version)
    #         # pub.sendMessage(cn.CN_TOPIC_DIR_CHG, dir_name=self.dir_name, added=added, deleted=deleted)

    def open_menu(self, position):
        menu = QMenu()
        menu.addAction(self.mf.menu.actions[GuiAttr.NEW_TRACK_VERSION])
        menu.addAction(self.mf.menu.actions[GuiAttr.EDIT_TRACK_VERSION])
        menu.setDefaultAction(self.mf.menu.actions[GuiAttr.EDIT_TRACK_VERSION])
        menu.exec_(self.tab_box.tabBar().mapToGlobal(position))
        # menu.exec_(e.globalPos())

    @property
    def current_track_version(self) -> TrackVersion:
        track_tab: TrackTab = self.tab_box.currentWidget()
        if not track_tab:
            raise ValueError(f"Cannot determine tab with current track version. Track {self.track.name}")
        return track_tab.track_version

    @current_track_version.setter
    def current_track_version(self, track_version: TrackVersion) -> None:
        if self.tab_box.currentWidget() != self.map[track_version.version_name]:
            self.tab_box.setCurrentWidget(self.map[track_version.version_name])

    # def on_tab_changed(self, index: int):
    #     self.select_current_version(current_version=self.tab_box.widget(index).version_name)
    #
    # def select_current_version(self, current_version: str):
    #     if self.tab_box.currentWidget() != self.map[current_version]:
    #         self.tab_box.setCurrentWidget(self.map[current_version])
