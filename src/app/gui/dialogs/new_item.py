from __future__ import annotations

from enum import Enum, auto
from typing import TYPE_CHECKING

from PySide6.QtCore import Qt, QSize
from PySide6.QtGui import QColor, QPalette
from PySide6.QtWidgets import (
    QDialog,
    QDialogButtonBox,
    QBoxLayout,
    QFormLayout,
    QLineEdit,
    QAbstractButton,
    QCheckBox,
    QToolButton,
    QColorDialog,
)

from src.app.model.sequence import Sequence
from src.app.utils.properties import MidiAttr, GuiAttr, Color
from src.app.gui.widgets import Box, ChannelBox
from src.app.model.composition import Composition
from src.app.model.project import Project
from src.app.model.track import Track, TrackVersion

if TYPE_CHECKING:
    from src.app.gui.main_frame import MainFrame


class NewItemDlg(QDialog):
    def __init__(
        self,
        mf: MainFrame,
        project: Project = None,
        composition: Composition = None,
        track: Track = None,
    ):
        super().__init__(parent=mf)
        self.mf = mf
        self.project = project
        self.composition = composition
        self.track = track
        self.set_title()
        # self.setSizeGripEnabled(True)
        self.buttons = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel, Qt.Horizontal)
        self.main_box = Box(direction=QBoxLayout.TopToBottom)
        self.main_box.setContentsMargins(5, 5, 5, 5)
        self._main_layout = self.get_main_layout(composition=self.composition, track=self.track)
        self.main_box.addLayout(self.main_layout)
        self.main_box.addWidget(self.buttons)
        self.setLayout(self.main_box)

        self.buttons.clicked.connect(self.button_clicked)
        self.setMinimumSize(QSize(500, self.height()))

    @property
    def main_layout(self) -> NewNameForm:
        return self._main_layout

    def button_clicked(self, button: QAbstractButton):
        if self.buttons.buttonRole(button) == QDialogButtonBox.AcceptRole:
            if self.main_layout.is_valid():
                self.accept()
        else:
            self.reject()

    def get_main_layout(self, composition: Composition, track: Track):
        raise NotImplementedError

    def set_title(self):
        pass

    def get_name(self) -> str:
        return self.main_layout.get_name()


class NewNameForm(QFormLayout):
    def __init__(self, mf: MainFrame, label: str):
        super().__init__()
        self.mf = mf
        self.setContentsMargins(10, 10, 10, 10)
        self.setSpacing(5)
        self.name = QLineEdit()
        self.addRow(label, self.name)

    def get_name(self):
        return self.name.text().strip()

    def is_valid(self) -> bool:
        return self.name.text().strip() != ""


class TrackEditMode(Enum):
    new_track = auto()
    edit_track = auto()
    new_track_version = auto()
    edit_track_version = auto()


class NewTrackForm(NewNameForm):
    def __init__(
        self,
        mf: MainFrame,
        mode: TrackEditMode,
        composition: Composition,
        track: Track,
        track_version: TrackVersion,
    ):
        super().__init__(mf=mf, label="Track name")
        self.mf = mf
        self.mode = mode
        self.composition = composition
        self.track = track
        self.track_version = track_version
        self.track_color = QToolButton()
        self.addRow("Track color", self.track_color)
        self.version_name = QLineEdit()
        self.addRow("Version name", self.version_name)
        self.version_channel = ChannelBox(default_channel=self.get_default_channel())
        self.addRow("Version channel", self.version_channel)
        self.enable_in_loops = QCheckBox("Enable track in loops")
        self.enable_in_loops.setChecked(True)
        self.addRow("", self.enable_in_loops)

        self.init_ui()
        self.track_color.clicked.connect(self.get_track_color)

    def init_ui(self):
        self.name.setText(self.track.name if self.mode == TrackEditMode.edit_track else "")
        self.name.setEnabled(self.mode in (TrackEditMode.new_track, TrackEditMode.edit_track))
        self.show_track_color(color=QColor.fromRgba(self.track.default_color) if self.track else Color.NODE_START)
        self.track_color.setEnabled(self.mode in (TrackEditMode.new_track, TrackEditMode.edit_track))
        self.version_name.setText(
            self.track_version.version_name
            if self.track_version
            else GuiAttr.DEFAULT_VERSION_NAME
            if not self.track
            else ""
        )
        self.version_name.setEnabled(self.mode in (TrackEditMode.new_track_version, TrackEditMode.edit_track_version))
        self.version_channel.setCurrentIndex(
            self.track_version.channel
            if self.track_version
            else self.track.default_channel
            if self.track
            else self.composition.get_next_free_channel()
        )
        self.version_channel.setEnabled(
            self.mode in (TrackEditMode.new_track_version, TrackEditMode.edit_track_version)
        )

    def get_track_color(self):
        color = QColorDialog.getColor(
            self.track_color.default if hasattr(self.track_color, GuiAttr.DEFAULT) else Color.NODE_START
        )
        if color:
            self.track_color.default = color.rgba()
            self.show_track_color(color=color)

    def show_track_color(self, color: QColor):
        self.track_color.setAutoFillBackground(True)
        pal = self.track_color.palette()
        pal.setColor(QPalette.Button, color)
        self.track_color.setPalette(pal)

    def is_track_name_valid(self) -> bool:
        valid = self.get_name() != ""
        if not valid:
            self.mf.show_message_box("Track name is empty")
            return valid
        valid = not self.composition.track_name_exists(track_name=self.get_name())
        if not valid:
            self.mf.show_message_box(f"Track name {self.get_name()} exists in composition")
        return valid

    def is_track_version_name_valid(self) -> bool:
        valid = self.get_version_name() != ""
        if not valid:
            self.mf.show_message_box("Version name is empty")
        return valid

    def is_valid(self) -> bool:
        return self.is_track_name_valid() and self.is_track_version_name_valid()

    def get_version_name(self) -> str:
        return self.version_name.text().strip()

    def get_default_channel(self):
        return self.composition.get_first_track_version().channel

    def get_default_num_of_bars(self):
        return self.composition.get_first_track_version().num_of_bars()


class NewTrackDlg(NewItemDlg):
    def __init__(
        self,
        mf: MainFrame,
        mode: TrackEditMode,
        project: Project = None,
        composition: Composition = None,
        track: Track = None,
        track_version: TrackVersion = None,
    ):
        self.mode = mode
        self.track_version = track_version
        super().__init__(mf=mf, project=project, composition=composition, track=track)

    @property
    def main_layout(self) -> NewTrackForm:
        return self._main_layout

    def get_main_layout(self, composition: Composition, track: Track):
        return NewTrackForm(
            mf=self.mf,
            mode=self.mode,
            composition=composition,
            track=track,
            track_version=self.track_version,
        )

    def set_title(self):
        self.setWindowTitle(f"Add new track in {self.composition.name} composition")

    def get_enable_track_in_loops(self) -> bool:
        return self.main_layout.enable_in_loops.isChecked()

    def get_track(self):
        ml: NewTrackForm = self.main_layout
        track_version = TrackVersion(
            channel=ml.version_channel.get_channel(),
            version_name=ml.get_version_name(),
            sf_name=MidiAttr.DEFAULT_SF2,
            sequence=Sequence.from_num_of_bars(num_of_bars=ml.get_default_num_of_bars()),
        )
        return Track(
            name=ml.get_name(),
            current_version=ml.get_version_name(),
            versions={ml.get_version_name(): track_version},
        )
