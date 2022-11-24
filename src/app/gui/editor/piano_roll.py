from __future__ import annotations

import logging
from typing import TYPE_CHECKING
from typing import Tuple

from PySide6.QtCore import Qt
from PySide6.QtGui import QKeySequence
from PySide6.QtWidgets import QWidget, QBoxLayout
from pydantic import PositiveInt

from src.app.backend.midway_synth import MidwaySynth
from src.app.gui.editor.base_grid import BaseGridView, KeyboardGridBox
from src.app.gui.editor.grid import GridScene
from src.app.gui.editor.ruler import HeaderView, RulerScene
from src.app.gui.menu import Action
from src.app.gui.widgets import Box
from src.app.model.project_version import ProjectVersion
from src.app.model.sequence import Sequence
from src.app.model.track import TrackVersion, Track
from src.app.model.types import Bpm, Channel
from src.app.utils.logger import get_console_logger

if TYPE_CHECKING:
    from src.app.gui.main_frame import MainFrame

logger = get_console_logger(name=__name__, log_level=logging.DEBUG)


class PianoRoll(QWidget):
    # pylint: disable=duplicate-code
    def __init__(
        self,
        mf: MainFrame,
        parent,
        track_version: TrackVersion,
        synth: MidwaySynth,
        project_version: ProjectVersion,
        track: Track,
    ):
        super().__init__(parent=parent)
        self.mf = mf
        self.project_version = project_version
        self.track = track
        self.track_version = track_version
        self.synth = synth
        self.setAutoFillBackground(True)
        self.grid_view = BaseGridView(
            cls=GridScene,
            num_of_bars=self.num_of_bars,
            channel=track_version.channel,
            synth=synth,
            track_version=track_version,
        )
        self.grid_view.verticalScrollBar().valueChanged.connect(self.on_change_ver)
        self.grid_view.horizontalScrollBar().valueChanged.connect(self.on_change_hor)
        self.grid_view.keyboard_view.verticalScrollBar().valueChanged.connect(self.on_change_ver)
        self.grid_view.keyboard_view.horizontalScrollBar().valueChanged.connect(self.on_change_hor)
        self.ruler_view = BaseGridView(
            cls=RulerScene,
            num_of_bars=self.num_of_bars,
            channel=track_version.channel,
            synth=synth,
            track_version=track_version,
        )
        self.header_view = HeaderView(keyboard_=self.ruler_view.keyboard_view.keyboard)
        self.box_main = Box(direction=QBoxLayout.TopToBottom)
        self.box_main.addLayout(KeyboardGridBox([self.header_view, self.ruler_view]))
        self.box_main.addLayout(KeyboardGridBox([self.grid_view.keyboard_view, self.grid_view]))

        self.ac_select_all = Action(
            mf=self.mf,
            caption="Select all",
            shortcut=QKeySequence.SelectAll,
            slot=self.select_all,
        )
        self.ac_delete = Action(
            mf=self.mf,
            caption="Delete selected",
            shortcut=QKeySequence.Delete,
            slot=self.delete_selected,
        )
        self.ac_invert_sel = Action(
            mf=self.mf,
            caption="Invert selection",
            shortcut=QKeySequence(Qt.CTRL | Qt.Key_I),
            slot=self.invert_selection,
        )
        self.ac_copy_sel = Action(
            mf=self.mf,
            caption="Copy selection",
            shortcut=QKeySequence.Copy,
            slot=self.copy_selection,
        )
        # self.ac_play = Action(
        #     mf=self.mf,
        #     caption="Play piano roll sequence",
        #     shortcut=QKeySequence(Qt.Key_Enter),
        #     slot=self.play,
        # )
        self.ac_escape = Action(mf=self.mf, caption="Escape", shortcut=QKeySequence.Cancel, slot=self.escape)

        self.setLayout(self.box_main)
        self.sequence = self.track_version.sequence
        assert self.sequence is not None

    # def play(self, mf: MainFrame):
    #     loop = self.project_version.loops[LoopType.custom].get_loop_by_name(loop_name=GuiAttr.SINGLE_TRACK)
    #     loop.set_single_track_version(track=self.track, track_version=self.track_version)
    #     logger.debug("playing")
    #     self.synth.play_composition(
    #         self.project_version, loop_type=LoopType.custom, loop_name=GuiAttr.SINGLE_TRACK, bpm=mf.project.bpm
    #     )

    def select_all(self, _: MainFrame):
        self.grid_view.grid_scene.select_all()

    def delete_selected(self, _: MainFrame):
        self.grid_view.grid_scene.delete_nodes(meta_notes=self.grid_view.grid_scene.selected_nodes(), hard_delete=True)

    def invert_selection(self, _: MainFrame):
        self.grid_view.grid_scene.invert_selection()

    def copy_selection(self, _: MainFrame):
        self.grid_view.grid_scene.copy_selection()

    def escape(self, _: MainFrame):
        self.grid_view.grid_scene.escape()

    def undo(self, mf: MainFrame):
        pass

    @property
    def bpm(self) -> Bpm:
        return self.mf.project.bpm

    @property
    def channel(self) -> Channel:
        return self.track_version.channel

    @channel.setter
    def channel(self, value: Channel) -> None:
        self.track_version.channel = value

    @property
    def sequence(self) -> Sequence:
        return self.track_version.sequence

    @sequence.setter
    def sequence(self, value: Sequence) -> None:
        self.track_version.sequence = value
        self.ruler_view.grid_scene.sequence = value
        self.grid_view.grid_scene.sequence = value

    @property
    def num_of_bars(self) -> PositiveInt:
        return self.track_version.num_of_bars()

    @num_of_bars.setter
    def num_of_bars(self, value) -> None:
        self.ruler_view.num_of_bars = value
        self.grid_view.num_of_bars = value
        self.sequence.set_num_of_bars(value=value)
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
        self.synth.sfont_select(self.track_version.channel, self.synth.sfid(name))

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
        self.synth.program_select(self.track_version.channel, self.synth.sfid(self.sf_name), bank, patch)

    def on_change_ver(self, value: int):
        self.grid_view.keyboard_view.verticalScrollBar().setValue(value)
        self.grid_view.verticalScrollBar().setValue(value)

    def on_change_hor(self, value: int):
        self.ruler_view.horizontalScrollBar().setValue(value)
        self.grid_view.horizontalScrollBar().setValue(value)
