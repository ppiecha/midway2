from __future__ import annotations
import logging
import threading
from pathlib import Path
from typing import Optional, TYPE_CHECKING
from PySide6.QtCore import Qt
from PySide6.QtGui import QPainter
from PySide6.QtWidgets import (
    QWidget,
    QBoxLayout,
    QGraphicsView,
    QFrame,
    QCheckBox,
    QComboBox,
    QFormLayout,
    QSpinBox,
    QLineEdit,
    QToolButton,
)


from src.app.model.project import Project
from src.app.model.project_version import ProjectVersion
from src.app.utils.logger import get_console_logger
from src.app.utils.notification import register_listener
from src.app.utils.properties import MidiAttr, NotificationMessage
from src.app.backend.midway_synth import MidwaySynth
from src.app.model.types import Preset
from src.app.model.track import Track, TrackVersion

# from src.app.model.variant_item import Loop, VariantItem, LoopType

if TYPE_CHECKING:
    from src.app.gui.main_frame import MainFrame
    from src.app.model.project_version import ProjectVersion
    from src.app.gui.menu import Action

logger = get_console_logger(name=__name__, log_level=logging.DEBUG)


class SafeThread(threading.Thread):
    """ShellThread should always e used in preference to threading.Thread.
    The interface provided by ShellThread is identical to that of threading.Thread,
    however, if an exception occurs in the thread the error will be logged
    to the user rather than printed to stderr.
    """

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self._real_run = self.run
        self.run = self._wrap_run

    def _wrap_run(self):
        try:
            logger.debug("Thread started")
            self._real_run()
            logger.debug("Thread stopped")
        except Exception as e:
            logger.error(str(e))
            raise e


class Box(QBoxLayout):
    def __init__(self, direction):
        super().__init__(direction)
        self.setContentsMargins(0, 0, 0, 0)
        # self.setMargin(0)
        self.setSpacing(0)


class GraphicsView(QGraphicsView):
    def __init__(self, show_scrollbars: bool = False):
        super().__init__()
        self.setMouseTracking(True)
        self.setContentsMargins(0, 0, 0, 0)
        self.setViewportMargins(0, 0, 0, 0)
        self.setContentsMargins(0, 0, 0, 0)
        self.setFrameShape(QFrame.NoFrame)
        self.setRenderHint(QPainter.Antialiasing)
        self.setAlignment(Qt.AlignTop | Qt.AlignLeft)
        self.horizontalScrollBar().setContentsMargins(0, 0, 0, 0)
        self.verticalScrollBar().setContentsMargins(0, 0, 0, 0)
        if not show_scrollbars:
            self.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
            self.setVerticalScrollBarPolicy(Qt.ScrollBarAlwaysOff)


class BarBox(QSpinBox):
    def __init__(self, parent=None):
        super().__init__(parent=parent)
        self.setMinimum(1)


class ChannelBox(QComboBox):
    def __init__(self, default_channel: int = None):
        super().__init__()
        for channel in MidiAttr.CHANNELS:
            if channel == 9:
                self.addItem(f"Drums (channel {channel})")
            else:
                self.addItem(f"Channel {str(channel)}", channel)
        if default_channel:
            self.setCurrentIndex(default_channel)

    def get_channel(self):
        return self.currentIndex()


class FontBox(QComboBox):
    def __init__(self, synth: MidwaySynth):
        super().__init__()
        self.synth = synth

    def populate_font_combo(self):
        self.setEditable(False)
        self.setDuplicatesEnabled(False)
        self.clear()
        for font in self.synth.sf_map.keys():
            self.addItem(Path(font).name, font)


class PresetBox(QComboBox):
    def __init__(self, synth: MidwaySynth):
        super().__init__()
        self.synth = synth

    def populate_preset_combo(self, sfid: int):
        self.clear()
        for bank in self.synth.preset_map[sfid]:
            for patch in self.synth.preset_map[sfid][bank]:
                sf_name = self.synth.sf_name(sfid=sfid)
                preset = Preset(sf_name=sf_name, bank=bank, patch=patch)
                preset_map = self.synth.preset_map
                if sfid in preset_map and bank in preset_map[sfid] and patch in preset_map[sfid][bank]:
                    preset_name = preset_map[sfid][bank][patch]
                    self.addItem(f"{bank}:{patch} {preset_name}", preset)


class DeriveTrackVersionBox(QWidget):
    def __init__(self, parent, mf: MainFrame):
        super().__init__(parent)
        self.mf = mf
        self.form = QFormLayout()
        self.init_project_version: Optional[ProjectVersion] = None
        self.init_track: Optional[Track] = None
        self.init_track_version: Optional[TrackVersion] = None
        self.project_version_box = QComboBox()
        self.track_box = QComboBox()
        self.track_version_box = QComboBox()
        self.derive_ctrl_events = QCheckBox("Derive control events")
        self.form = QFormLayout()
        self.form.setLabelAlignment(Qt.AlignRight)
        self.form.setContentsMargins(10, 10, 10, 10)
        self.form.setSpacing(5)
        self.form.setAlignment(Qt.AlignLeft)
        self.form.addRow("Project version", self.project_version_box)
        self.form.addRow("Track", self.track_box)
        self.form.addRow("Track version", self.track_version_box)
        self.form.addRow("", self.derive_ctrl_events)
        self.frame = QFrame()
        self.frame.setFrameStyle(QFrame.StyledPanel | QFrame.Plain)
        self.main_box = Box(QBoxLayout.TopToBottom)
        self.main_box.addLayout(self.form)
        self.frame.setLayout(self.main_box)
        self.frame_box = Box(QBoxLayout.TopToBottom)
        self.frame_box.addWidget(self.frame)
        self.setLayout(self.frame_box)

        self.project_version_box.currentIndexChanged.connect(self.on_project_version_changed)
        self.track_box.currentIndexChanged.connect(self.on_track_changed)

    def get_derived_version(self) -> TrackVersion:
        project_version = self.mf.project.get_version_by_name(version_name=self.project_version_box.currentText())
        track = project_version.tracks.get_track(identifier=self.track_box.currentText())
        track_version = track.get_version(identifier=self.track_version_box.currentText())
        track_version = TrackVersion(**track_version.__dict__)
        if not self.derive_ctrl_events.isChecked():
            pass  # remove ctrl events
        return track_version

    def on_project_version_changed(self, index):
        if index >= 0:
            project_version = self.mf.project.get_version_by_name(version_name=self.project_version_box.itemText(index))
            if project_version:
                self.load_tracks(project_version=project_version, track=self.init_track)

    def on_track_changed(self, index):
        if index >= 0:
            project_version = self.mf.project.get_version_by_name(version_name=self.project_version_box.currentText())
            track = project_version.tracks.get_track(identifier=self.track_box.itemText(index))
            if track:
                self.load_track_version(track=track, track_version=self.init_track_version)
            else:
                raise ValueError("Track not found")

    def load_project_versions(
        self,
        project: Optional[Project],
        init_project_version: Optional[ProjectVersion],
        init_track: Optional[Track],
        init_track_version: Optional[TrackVersion],
    ):
        self.init_project_version = init_project_version
        self.init_track = init_track
        self.init_track_version = init_track_version
        self.project_version_box.clear()
        if project is not None:
            self.project_version_box.addItems([version.name for version in project.versions])
            if init_project_version is not None:
                self.project_version_box.setCurrentText(init_project_version.name)

    def load_tracks(self, project_version: Optional[ProjectVersion], track: Optional[Track]):
        self.track_box.clear()
        if project_version is not None:
            self.track_box.addItems([track.name for track in project_version.tracks])
            if track is not None:
                self.track_box.setCurrentText(track.name)

    def load_track_version(self, track: Optional[Track], track_version: Optional[TrackVersion]):
        self.track_version_box.clear()
        if track is not None:
            self.track_version_box.addItems([version.name for version in track.versions])
            if track_version is not None:
                self.track_version_box.setCurrentText(track_version.name)


class EditBox(QLineEdit):
    def __init__(self, default: Optional[str] = ""):
        super().__init__()
        self.setText(default)


class PlayButton(QToolButton):
    def __init__(self, parent: QWidget, mf: MainFrame, project_version: ProjectVersion):
        super().__init__(parent)
        self.mf = mf
        self.project_version = project_version

        # register_listener(mapping={NotificationMessage.PLAY: None, NotificationMessage.STOP: None})

    def play_action(self, project_version: ProjectVersion) -> Action:
        pass
