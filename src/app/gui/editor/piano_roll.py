from __future__ import annotations

import logging
from typing import Tuple

from PySide6.QtCore import Qt
from PySide6.QtGui import QKeySequence
from PySide6.QtWidgets import QWidget, QBoxLayout

from src.app.utils.constants import SINGLE_TRACK
from src.app.gui.menu import Action
from src.app.gui.editor.grid import GridView
from src.app.gui.editor.keyboard import KeyboardView
from src.app.gui.editor.ruler import RulerView, HeaderView
from src.app.gui.widgets import Box
from src.app.utils.logger import get_console_logger
from src.app.backend.midway_synth import MidwaySynth
from src.app.model.event import Bpm
from src.app.model.loop import LoopType
from src.app.model.composition import Composition
from src.app.model.sequence import Sequence
from src.app.model.track import TrackVersion, Track

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from src.app.gui.main_frame import MainFrame

logger = get_console_logger(name=__name__, log_level=logging.DEBUG)


class PianoRoll(QWidget):
    def __init__(self, mf: MainFrame, parent, track_version: TrackVersion,
                 synth: MidwaySynth, composition: Composition,
                 track: Track):
        super().__init__(parent=parent)
        self.mf = mf
        self.composition = composition
        self.track = track
        self.track_version = track_version
        self.synth = synth
        self.setAutoFillBackground(True)
        self.grid_view = GridView(num_of_bars=self.num_of_bars,
                                  channel=track_version.channel)
        self.grid_view.verticalScrollBar().valueChanged.connect(
            self.on_change_ver)
        self.grid_view.horizontalScrollBar().valueChanged.connect(
            self.on_change_hor)
        self.keyboard = KeyboardView(channel=self.channel,
                                     callback=self.grid_view.mark, synth=synth)
        self.keyboard.verticalScrollBar().valueChanged.connect(
            self.on_change_ver)
        self.keyboard.horizontalScrollBar().valueChanged.connect(
            self.on_change_hor)
        self.grid_view.grid_scene.keyboard_view = self.keyboard
        self.ruler_view = RulerView(channel=self.channel,
                                    num_of_bars=self.num_of_bars,
                                    grid_view=self.grid_view)
        self.header_view = HeaderView()
        self.box_piano = Box(direction=QBoxLayout.LeftToRight)
        self.box_piano.addWidget(self.keyboard)
        self.box_piano.addWidget(self.grid_view)
        self.box_ruler = Box(direction=QBoxLayout.LeftToRight)
        self.box_ruler.addWidget(self.header_view)
        self.box_ruler.addWidget(self.ruler_view)
        self.box_main = Box(direction=QBoxLayout.TopToBottom)
        self.box_main.addLayout(self.box_ruler)
        self.box_main.addLayout(self.box_piano)

        self.ac_select_all = Action(mf=self.mf, caption="Select all",
                                    shortcut=QKeySequence.SelectAll,
                                    slot=self.select_all)
        self.ac_delete = Action(mf=self.mf, caption="Delete selected",
                                shortcut=QKeySequence.Delete,
                                slot=self.delete_selected)
        self.ac_invert_sel = Action(mf=self.mf, caption="Invert selection",
                                    shortcut=QKeySequence(Qt.CTRL | Qt.Key_I),
                                    slot=self.invert_selection)
        self.ac_copy_sel = Action(mf=self.mf, caption="Copy selection",
                                  shortcut=QKeySequence.Copy,
                                  slot=self.copy_selection)
        self.ac_play = Action(mf=self.mf, caption="Play pianoroll sequence",
                              shortcut=QKeySequence(Qt.Key_Enter),
                              slot=self.play)
        self.ac_escape = Action(mf=self.mf, caption="Escape",
                                shortcut=QKeySequence.Cancel, slot=self.escape)

        self.setLayout(self.box_main)
        self.sequence = self.track_version.sequence

    def play(self, mf: MainFrame):
        loop = self.composition.loops[LoopType.custom].get_loop_by_name(
            loop_name=SINGLE_TRACK)
        loop.set_single_track_version(track=self.track,
                                      track_version=self.track_version)
        self.synth.play_composition(self.composition,
                                    loop_type=LoopType.custom,
                                    loop_name=SINGLE_TRACK)

    def select_all(self, mf: MainFrame):
        self.grid_view.grid_scene.select_all()

    def delete_selected(self, mf: MainFrame):
        self.grid_view.grid_scene.delete_nodes(
            meta_notes=self.grid_view.grid_scene.selected_notes,
            hard_delete=True)

    def invert_selection(self, mf: MainFrame):
        self.grid_view.grid_scene.invert_selection()

    def copy_selection(self, mf: MainFrame):
        self.grid_view.grid_scene.copy_selection()

    def escape(self, mf: MainFrame):
        self.grid_view.grid_scene.escape()

    def undo(self, mf: MainFrame):
        pass

    @property
    def bpm(self) -> Bpm:
        return self.mf.project.bpm

    @property
    def channel(self) -> int:
        return self.track_version.channel

    @channel.setter
    def channel(self, value: int) -> None:
        self.track_version.channel = value

    @property
    def sequence(self):
        return self.track_version.sequence

    @sequence.setter
    def sequence(self, value: Sequence) -> None:
        self.track_version.sequence = value
        self.ruler_view.ruler_scene.sequence = value
        self.grid_view.grid_scene.sequence = value

    @property
    def num_of_bars(self) -> int:
        return self.track_version.num_of_bars

    @num_of_bars.setter
    def num_of_bars(self, value) -> None:
        self.track_version.num_of_bars = value
        self.ruler_view.num_of_bars = value
        self.grid_view.num_of_bars = value
        self.sequence.set_num_of_bars(value=value - 1)
        self.grid_view.horizontalScrollBar().setValue(1)
        self.grid_view.horizontalScrollBar().setValue(0)

    @property
    def sf_name(self) -> str:
        # preset = self.synth.get_current_preset(channel=self.track_version.channel)
        # return self.synth.sf_name(sfid=preset.sfid)
        return self.track_version.sf_name

    @sf_name.setter
    def sf_name(self, name: str):
        self.track_version.sf_name = name
        self.synth.sfont_select(self.track_version.channel,
                                self.synth.sfid(name))

    @property
    def bank_patch(self):
        # preset = self.synth.get_current_preset(channel=self.track_version.channel)
        # return preset.bank, preset.patch
        return self.track_version.bank, self.track_version.patch

    @bank_patch.setter
    def bank_patch(self, value: Tuple[int, int]):
        bank, patch = value
        self.track_version.bank = bank
        self.track_version.patch = patch
        self.synth.program_select(self.track_version.channel,
                                  self.synth.sfid(self.sf_name), bank, patch)

    def on_change_ver(self, value: int):
        self.keyboard.verticalScrollBar().setValue(value)
        self.grid_view.verticalScrollBar().setValue(value)

    def on_change_hor(self, value: int):
        self.ruler_view.horizontalScrollBar().setValue(value)
        self.grid_view.horizontalScrollBar().setValue(value)
