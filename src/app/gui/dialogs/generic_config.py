from __future__ import annotations

from enum import auto, Enum
from pathlib import Path
from typing import Any, NamedTuple

from PySide6.QtCore import QSize

from src.app.gui.editor.keyboard import PianoKeyboardView, PianoKeyboardWidget
from typing import TYPE_CHECKING

from src.app.model.sequence import Sequence
from src.app.utils.properties import Color, GuiAttr, IniAttr, MidiAttr

if TYPE_CHECKING:
    from src.app.gui.editor.node import Node

from src.app.model.composition import Composition
from src.app.model.event import Preset
from src.app.model.types import Channel
from src.app.model.project import Project
from src.app.model.track import TrackVersion, Track

if TYPE_CHECKING:
    from src.app.gui.main_frame import MainFrame
from typing import Optional

from PySide6.QtGui import Qt, QIcon, QColor, QPalette
from PySide6.QtWidgets import (
    QWidget,
    QDialog,
    QBoxLayout,
    QTabWidget,
    QSplitter,
    QListWidget,
    QListWidgetItem,
    QToolButton,
    QLineEdit,
    QCheckBox,
    QColorDialog,
    QFormLayout,
    QDialogButtonBox,
    QAbstractButton,
)

from src.app.gui.widgets import Box, ChannelBox, DeriveTrackVersionBox, BarBox
import src.app.resources


class GenericConfigMode(int, Enum):
    new_track = auto()
    edit_track = auto()
    new_track_version = auto()
    edit_track_version = auto()


class GenericConfig(NamedTuple):
    mf: MainFrame
    mode: Optional[GenericConfigMode] = None
    project: Optional[Project] = None
    composition: Optional[Composition] = None
    track: Optional[Track] = None
    track_version: Optional[TrackVersion] = None
    node: Optional[Node] = None


class GenericConfigDlg(QDialog):
    def __init__(self, mf: MainFrame):
        super().__init__(parent=mf)
        self.mf = mf
        self.config: Optional[GenericConfig] = None
        self.setSizeGripEnabled(True)
        self.tab_box = QTabWidget()
        self.general = GeneralTab(gen_conf_dlg=self)
        self.preset = PresetTab(gen_conf_dlg=self)
        self.tab_map = {
            GuiAttr.GENERAL: self.tab_box.addTab(self.general, GuiAttr.GENERAL),
            GuiAttr.PRESET: self.tab_box.addTab(self.preset, GuiAttr.PRESET),
        }
        self.buttons = QDialogButtonBox(
            QDialogButtonBox.Ok | QDialogButtonBox.Cancel, Qt.Horizontal
        )
        self.main_box = Box(direction=QBoxLayout.TopToBottom)
        self.main_box.setContentsMargins(10, 10, 10, 10)
        self.main_box.setSpacing(10)
        self.main_box.addWidget(self.tab_box)
        self.main_box.addWidget(self.buttons)
        self.setLayout(self.main_box)

        self.buttons.clicked.connect(self.button_clicked)

    def button_clicked(self, button: QAbstractButton):
        if self.buttons.buttonRole(button) == QDialogButtonBox.AcceptRole:
            if self.general.is_valid():
                self.apply_changes()
                self.accept()
        else:
            self.reject()

    def apply_changes(self):
        if self.config.mode == GenericConfigMode.new_track:
            self.mf.project.composition_by_name(
                composition_name=self.config.composition.name, raise_not_found=True
            ).new_track(track=self.general.track, enable=True)
            self.config.mf.menu.post_new_track(
                composition=self.config.composition, track=self.general.track
            )

    def load_config(self, config: GenericConfig):
        self.config = GenericConfig(
            mf=config.mf,
            mode=config.mode,
            project=config.project,
            composition=config.composition,
            track=config.track,
            track_version=config.track_version,
            node=config.node,
        )
        self.setWindowTitle(
            f"Node settings" if self.config.node else f"General settings"
        )
        self.load_window_geometry(config=self.config)
        if self.config.node:
            self.tab_box.setTabEnabled(self.tab_map[GuiAttr.GENERAL], False)
        else:
            self.tab_box.setTabEnabled(self.tab_map[GuiAttr.GENERAL], True)
            self.general.load_config(config=self.config)
        self.preset.load_config(config=self.config)

    def load_window_geometry(self, config: GenericConfig):
        if not self.isVisible():
            size = config.mf.config.value(IniAttr.EVENT_WIN_SIZE, QSize(500, 400))
            pos = config.mf.config.value(IniAttr.EVENT_WIN_POS, None)
            if pos:
                self.setGeometry(pos.x(), pos.y(), size.width(), size.height())
            else:
                self.resize(size)

    def closeEvent(self, e):
        self.config.mf.config.setValue(IniAttr.EVENT_WIN_SIZE, self.size())
        self.config.mf.config.setValue(IniAttr.EVENT_WIN_POS, self.pos())


class PresetTab(QWidget):
    def __init__(self, gen_conf_dlg):
        super().__init__(parent=gen_conf_dlg)
        self.config: Optional[GenericConfig] = None
        self.sf_list = QListWidget()
        self.sf_list.resize(280, self.sf_list.height())
        self.bank_list = QListWidget()
        self.bank_list.resize(50, self.bank_list.height())
        self.prog_list = QListWidget()
        self.keyboard = PianoKeyboardView(
            cls=PianoKeyboardWidget, synth=None, channel=self.channel, callback=None
        )
        self.splitter_right = QSplitter(Qt.Horizontal)
        self.splitter_right.addWidget(self.bank_list)
        self.splitter_right.addWidget(self.prog_list)
        self.splitter_right.addWidget(self.keyboard)
        self.splitter = QSplitter(Qt.Horizontal)
        self.splitter.addWidget(self.sf_list)
        self.splitter.addWidget(self.splitter_right)
        self.main_box = Box(direction=QBoxLayout.LeftToRight)
        self.main_box.addWidget(self.splitter)
        self.setLayout(self.main_box)

        self.sf_list.itemSelectionChanged.connect(self.on_sf_change)
        self.bank_list.itemSelectionChanged.connect(self.on_bank_change)
        self.prog_list.itemActivated.connect(self.on_prog_activated)
        self.prog_list.currentItemChanged.connect(self.on_prog_selected)

    @property
    def channel(self) -> Channel:
        return MidiAttr.MAX_CHANNEL - 1

    def load_config(self, config: GenericConfig):
        self.config = config
        self.keyboard.set_synth_and_channel(synth=config.mf.synth, channel=self.channel)
        self.populate_fonts()

    def set_initial_preset(self) -> None:
        if self.config.track_version:
            init_sf_name = self.config.track_version.sf_name
            init_bank = self.config.track_version.bank
            init_patch = self.config.track_version.patch
        elif self.config.track:
            init_sf_name = self.config.track.default_sf
            init_bank = self.config.track.default_bank
            init_patch = self.config.track.default_patch
        else:
            init_sf_name = MidiAttr.DEFAULT_SF2
            init_bank = MidiAttr.DEFAULT_BANK
            init_patch = MidiAttr.DEFAULT_PATCH
        self.select_data(lst=self.sf_list, data=init_sf_name)
        items = self.bank_list.findItems(str(init_bank), Qt.MatchExactly)
        if items:
            bank = self.bank_list.indexFromItem(items[0]).row()
        else:
            bank = 0
        if self.bank_list.count():
            self.bank_list.setCurrentRow(bank)
            self.bank_list.scrollToItem(self.bank_list.currentItem())
            if self.prog_list.count():
                self.select_data(
                    self.prog_list,
                    Preset(sf_name=init_sf_name, bank=bank, patch=init_patch),
                )

    @staticmethod
    def select_data(lst: QListWidget, data: Any) -> None:
        for row in range(lst.count()):
            item = lst.item(row)
            if item.data(Qt.UserRole) == data:
                lst.setCurrentItem(item)
                lst.scrollToItem(item)
                return
        raise ValueError(f"Cannot find data {data} in list {lst}")

    def on_sf_change(self):
        if self.sf_list.currentItem():
            last_bank = (
                self.bank_list.currentItem().text()
                if self.bank_list.currentItem()
                else None
            )
            sf_name = self.sf_list.currentItem().data(Qt.UserRole)
            sfid = self.config.mf.synth.sfid(sf_name)
            # print('on_sf_change', sf_name, sfid)
            self.populate_banks(sfid=sfid)
            if self.bank_list.count() > 0:
                self.bank_list.setCurrentRow(0)
                if last_bank is not None:
                    if items := self.bank_list.findItems(last_bank, Qt.MatchExactly):
                        item, *rest = items
                        self.bank_list.setCurrentItem(item)
            self.bank_list.scrollToItem(self.bank_list.currentItem())

    def on_bank_change(self):
        if self.sf_list.currentItem() and self.bank_list.currentItem():
            sf_name = self.sf_list.currentItem().data(Qt.UserRole)
            sfid = self.config.mf.synth.sfid(sf_name)
            bank = self.bank_list.currentItem().text()
            # print('on_bank_change', sf_name, sfid, bank)
            self.populate_programs(sfid=sfid, bank=int(bank))
            if self.prog_list.count() > 0:
                self.prog_list.setCurrentRow(0)
                self.prog_list.scrollToItem(self.prog_list.currentItem())

    def on_prog_activated(self, item: QListWidgetItem):
        preset = item.data(Qt.UserRole)
        # self.config.track_version

    def on_prog_selected(self, current: QListWidgetItem, previous: QListWidgetItem):
        if current:
            preset = current.data(Qt.UserRole)
            self.config.mf.synth.preset_change(channel=self.channel, preset=preset)

    @property
    def current_preset(self) -> Preset:
        return self.config.mf.synth.get_current_preset(channel=self.channel)

    def populate_fonts(self):
        self.sf_list.itemSelectionChanged.disconnect()
        self.sf_list.clear()
        self.bank_list.clear()
        self.prog_list.clear()
        for sf_path in self.config.mf.synth.sf_map.keys():
            item = QListWidgetItem(Path(sf_path).name, self.sf_list)
            item.setIcon(QIcon(":/icons/sf.png"))
            item.setData(Qt.UserRole, sf_path)
            self.sf_list.addItem(item)
        self.sf_list.itemSelectionChanged.connect(self.on_sf_change)
        self.set_initial_preset()

    def populate_banks(self, sfid: int):
        curr_sf_name = self.sf_list.currentItem().data(Qt.UserRole)
        curr_sfid = self.config.mf.synth.sfid(curr_sf_name)
        self.bank_list.itemSelectionChanged.disconnect()
        if sfid == curr_sfid:
            self.bank_list.clear()
            for bank in self.config.mf.synth.preset_map[sfid].keys():
                item = QListWidgetItem(str(bank), self.bank_list)
                item.setIcon(QIcon(":/icons/bank.png"))
                self.bank_list.addItem(item)
        self.bank_list.itemSelectionChanged.connect(self.on_bank_change)

    def populate_programs(self, sfid: int, bank: int):
        self.prog_list.currentItemChanged.disconnect()
        if bank == int(self.bank_list.currentItem().text()):
            self.prog_list.clear()
            # print('populate_programs', sfid, bank)
            for patch, preset in self.config.mf.synth.preset_map[sfid][bank].items():
                item = QListWidgetItem(f"{str(patch)}: {preset}")
                item.setIcon(QIcon(":/icons/preset.png"))
                sf_name = self.config.mf.synth.sf_name(sfid=sfid)
                item.setData(
                    Qt.UserRole, Preset(sf_name=sf_name, bank=bank, patch=patch)
                )
                self.prog_list.addItem(item)
        self.prog_list.currentItemChanged.connect(self.on_prog_selected)


class GeneralTab(QWidget):
    def __init__(self, gen_conf_dlg: GenericConfigDlg):
        super().__init__(parent=gen_conf_dlg)
        self.gen_conf_dlg = gen_conf_dlg
        self.config: Optional[GenericConfig] = None
        self.form = QFormLayout()
        self.form.setContentsMargins(10, 10, 10, 10)
        self.form.setSpacing(5)
        self.project_name_box = QLineEdit()
        self.composition_name_box = QLineEdit()
        self.track_name_box = QLineEdit()
        self.track_color_box = QToolButton()
        self.version_name_box = QLineEdit()
        self.version_channel_box = ChannelBox()
        self.version_bars_box = BarBox()
        self.enable_inheritance_box = QCheckBox("Enable inheritance")
        self.inheritance_box = Box(QBoxLayout.LeftToRight)
        self.inheritance_box.addWidget(self.enable_inheritance_box)
        self.derive_form_box = DeriveTrackVersionBox(parent=self, mf=gen_conf_dlg.mf)
        self.derive_form_box.frame.hide()
        self.enable_in_loops_box = QCheckBox("Enable track in loops")

        # Form
        self.form.addRow("Project name", self.project_name_box)
        self.form.addRow("Composition name", self.composition_name_box)
        self.form.addRow("Track name", self.track_name_box)
        self.form.addRow("Track color", self.track_color_box)
        self.form.addRow("Version name", self.version_name_box)
        self.form.addRow("Version channel", self.version_channel_box)
        self.form.addRow("Number of bars", self.version_bars_box)
        self.form.addRow("Derive from track", self.inheritance_box)
        self.form.addRow("", self.derive_form_box)
        self.form.addRow("", self.enable_in_loops_box)

        self.setLayout(self.form)

        self.track_color_box.clicked.connect(self.get_track_color)
        self.enable_inheritance_box.stateChanged.connect(self.on_enable_inheritance)

    @property
    def preset(self) -> Preset:
        return self.gen_conf_dlg.preset.current_preset

    def on_enable_inheritance(self):
        self.derive_form_box.frame.setVisible(self.enable_inheritance_box.isChecked())

    def load_config(self, config: GenericConfig):
        self.config = config
        self.project_name_box.setText(config.mf.project.name)
        self.composition_name_box.setText(config.composition.name)
        self.track_name_box.setText(config.track.name if config.track else "")
        self.show_track_color(
            color=QColor.fromRgba(config.track.default_color)
            if config.track
            else Color.NODE_START
        )
        self.version_name_box.setText(
            config.track_version.version_name
            if config.track_version
            else GuiAttr.DEFAULT_VERSION_NAME
        )
        self.version_channel_box.setCurrentIndex(
            config.track_version.channel
            if config.track_version
            else self.default_channel
        )
        self.version_channel_box.setEnabled(False)
        self.version_bars_box.setValue(
            config.track_version.num_of_bars()
            if config.track_version
            else self.default_num_of_bars
        )
        self.enable_inheritance_box.setChecked(False)
        self.enable_inheritance_box.setEnabled(
            config.mode
            == (GenericConfigMode.new_track or GenericConfigMode.new_track_version)
        )
        self.derive_form_box.load_composition(
            selected_value=self.config.composition.name
        )
        self.enable_in_loops_box.setChecked(
            True
            if not config.track and config.mode == GenericConfigMode.new_track
            else False
        )
        self.enable_in_loops_box.setEnabled(config.mode == GenericConfigMode.new_track)

    def get_track_color(self):
        color = QColorDialog.getColor(
            self.track_color_box.default
            if hasattr(self.track_color_box, GuiAttr.DEFAULT)
            else Color.NODE_START
        )
        if color:
            self.track_color_box.default = color.rgba()
            self.show_track_color(color=color)

    def show_track_color(self, color: QColor):
        self.track_color_box.setAutoFillBackground(True)
        pal = self.track_color_box.palette()
        pal.setColor(QPalette.Button, color)
        self.track_color_box.setPalette(pal)

    def validate_track_name(self) -> bool:
        valid = self.track_name != ""
        if not valid:
            self.config.mf.show_message_box("Track name is empty")
            return valid
        if self.config.composition:
            valid = not self.config.composition.track_name_exists(
                track_name=self.track_name, current_track=self.config.track
            )
        if not valid:
            self.config.mf.show_message_box(
                f"Track name {self.track_name} exists in composition"
            )
        return valid

    def validate_version_name(self) -> bool:
        valid = self.version_name != ""
        if not valid:
            self.config.mf.show_message_box("Version name is empty")
            return valid
        if self.config.track:
            valid = not self.config.track.track_version_exists(
                version_name=self.version_name,
                current_version=self.config.track_version,
            )
        if not valid:
            self.config.mf.show_message_box(
                f"Track name {self.track_name} exists in composition"
            )
        return valid

    def is_valid(self) -> bool:
        return self.validate_track_name() and self.validate_version_name()

    @property
    def project_name(self) -> str:
        return self.project_name_box.text().strip()

    @property
    def composition_name(self) -> str:
        return self.composition_name_box.text().strip()

    @property
    def track_name(self) -> str:
        return self.track_name_box.text().strip()

    @property
    def track_color(self) -> int:
        return self.track_color_box.palette().color(QPalette.Button).rgba()

    @property
    def version_name(self) -> str:
        return self.version_name_box.text().strip()

    @property
    def channel(self) -> Channel:
        return self.version_channel_box.get_channel()

    @property
    def default_channel(self):
        return self.config.composition.get_first_track_version().channel

    @property
    def bars(self) -> int:
        return self.version_bars_box.value()

    @property
    def default_num_of_bars(self):
        return self.config.composition.get_first_track_version().num_of_bars

    @property
    def version(self) -> TrackVersion:
        return TrackVersion(
            channel=self.channel,
            version_name=self.version_name,
            num_of_bars=self.bars,
            sf_name=self.config.mf.synth.sf_name(self.preset.sfid),
            bank=self.preset.bank,
            patch=self.preset.patch,
            sequence=self.derive_form_box.get_derived_version()
            if self.enable_inheritance_box.isChecked()
            else Sequence(num_of_bars=self.bars),
        )

    @property
    def track(self) -> Track:
        return Track(
            name=self.track_name,
            versions=[self.version],
            default_color=self.track_color,
            default_sf=self.config.mf.synth.sf_name(sfid=self.preset.sfid),
            default_bank=self.preset.bank,
            default_patch=self.preset.patch,
        )
