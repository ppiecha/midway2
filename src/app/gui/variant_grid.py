from __future__ import annotations

from abc import ABC, abstractmethod
from enum import Flag, auto
from typing import Optional, TYPE_CHECKING, Dict

from PySide6.QtCore import Qt, QSize
from PySide6.QtGui import QIcon
from PySide6.QtWidgets import (
    QTableWidget,
    QWidget,
    QBoxLayout,
    QToolBar,
    QTableWidgetItem,
    QButtonGroup,
    QHeaderView,
    QCheckBox,
    QComboBox,
    QToolButton,
)

from src.app.gui.menu import Action
from src.app.gui.widgets import Box
from src.app.model.project_version import ProjectVersion
from src.app.model.track import Track
from src.app.model.types import ABCWidgetFinalMeta
from src.app.model.variant import Variant, VariantType, VariantItem
from src.app.utils.notification import register_listener
from src.app.utils.properties import NotificationMessage, MenuAttr, VariantGridRowIndex
import src.app.resources  # pylint: disable=unused-import

if TYPE_CHECKING:
    from src.app.gui.main_frame import MainFrame


class CellMode(Flag):
    SELECTOR = auto()
    PLAY = auto()
    VERSION = auto()


class VersionCombo(QComboBox):
    def __init__(self, parent, project_version: ProjectVersion, track: Track):
        super().__init__(parent)
        self.project_version = project_version
        self.track = track
        self.reload_versions(self.track.get_default_version_index())

    def reload_versions(self, version_index: Optional[int] = None):
        self.clear()
        self.addItems([version.name for version in self.track.versions])
        if version_index:
            self.setCurrentIndex(version_index)

    def showPopup(self) -> None:
        self.reload_versions()
        super().showPopup()


class GridCell(QWidget):
    def __init__(
        self,
        mf: MainFrame,
        parent,
        project_version: ProjectVersion,
        variant: Variant,
        variant_item: Optional[VariantItem],
        cell_mode: CellMode,
    ):
        super().__init__(parent)
        self.mf = mf
        self.project_version = project_version
        self.variant = variant
        self.variant_item = variant_item
        self.cell_mode = cell_mode
        self.track: Optional[Track] = None
        self.enabled: Optional[QCheckBox] = None
        self.play_button: Optional[QToolButton] = None
        self.version: Optional[VersionCombo] = None
        self.main_box = Box(direction=QBoxLayout.LeftToRight)
        self.main_box.setContentsMargins(5, 0, 0, 0)
        self.main_box.setSpacing(5)
        self.set_components()
        self.setLayout(self.main_box)

    @abstractmethod
    def play_action(self) -> Action:
        def play_slot():
            self.mf.synth.play(project_version=self.project_version, start_variant_id=self.variant.id)

        return Action(
            mf=self.mf,
            caption="Play variant",
            slot=play_slot,
            icon=QIcon(":/icons/play.png"),
            shortcut=None,
        )

    @abstractmethod
    def set_components(self):
        self.enabled = QCheckBox(self)
        self.play_button = QToolButton(self)
        self.play_button.setDefaultAction(self.play_action())
        self.enabled.setVisible(CellMode.SELECTOR in self.cell_mode)
        self.play_button.setVisible(CellMode.PLAY in self.cell_mode)
        self.main_box.addWidget(self.enabled)
        self.main_box.addWidget(self.play_button)
        self.main_box.setAlignment(Qt.AlignCenter)

        self.enabled.stateChanged.connect(self.on_enable_changed)

    @abstractmethod
    def on_enable_changed(self):
        pass


class VersionGridCell(GridCell):
    def set_components(self):
        super().set_components()
        if CellMode.VERSION not in self.cell_mode:
            raise ValueError(f"{str(CellMode.VERSION)} must be in {self.cell_mode} for {self.__class__.__name__}")
        if not self.variant_item:
            raise ValueError(f"Variant item must be defined for {self.__class__.__name__}")
        track_id = self.variant_item.track_id
        self.track = self.project_version.tracks.get_track(identifier=track_id, raise_not_found=True)
        self.version = VersionCombo(self, project_version=self.project_version, track=self.track)
        self.version.setVisible(CellMode.VERSION in self.cell_mode)
        self.main_box.addWidget(self.version)
        self.main_box.setAlignment(Qt.AlignLeft)

        self.version.currentIndexChanged.connect(self.version_changed)

    def version_changed(self, index):
        if index >= 0:
            self.variant_item.version_id = self.track.get_version_by_version_index(index=index).id
            print(self.variant_item.version_id)

    def on_enable_changed(self):
        self.variant_item.enabled = self.enabled.isChecked()

    def play_action(self) -> Action:
        def play_slot(_):
            track_version = self.track.get_version(identifier=self.variant_item.version_id)
            self.mf.synth.play_track_version(
                track=self.track,
                track_version=track_version,
                bpm=self.project_version.bpm,
                repeat=False,
            )

        return Action(
            mf=self.mf,
            caption="Play track version",
            slot=play_slot,
            icon=QIcon(":/icons/play.png"),
            shortcut=None,
        )


def cell_factory(
    mf: MainFrame,
    parent,
    project_version: ProjectVersion,
    variant: Variant,
    variant_item: Optional[VariantItem],
    cell_mode: CellMode,
) -> GridCell:
    if CellMode.VERSION in cell_mode:
        cls = VersionGridCell
    else:
        cls = GridCell
    return cls(
        mf=mf,
        parent=parent,
        project_version=project_version,
        variant=variant,
        variant_item=variant_item,
        cell_mode=cell_mode,
    )


class VariantGrid(QWidget, ABC, metaclass=ABCWidgetFinalMeta):
    def __init__(self, parent, mf: MainFrame, project_version: ProjectVersion):
        super().__init__(parent)
        self.mf = mf
        self.project_version = project_version
        self.table = QTableWidget(self)
        self.table.setAlternatingRowColors(True)
        self.track_header: Dict[str, QTableWidgetItem] = {}
        self.variant_header: Dict[str, QTableWidgetItem] = {}
        self.check_box_group = QButtonGroup(self.table)
        self.load_items()
        self.table.resizeColumnsToContents()
        # self.table.resizeRowsToContents()
        vertical_header = self.table.verticalHeader()
        vertical_header.setSectionResizeMode(QHeaderView.Fixed)
        vertical_header.setDefaultSectionSize(20)
        self.tool_bar = VariantToolbar(variant_grid=self)
        self.main_box = Box(direction=QBoxLayout.TopToBottom)
        self.main_box.setContentsMargins(5, 5, 5, 5)
        self.main_box.addWidget(self.tool_bar)
        self.main_box.addWidget(self.table)
        self.setLayout(self.main_box)

    def get_track_header(self, track: Track) -> QTableWidgetItem:
        if item := self.track_header.get(track.name) is None:
            item = QTableWidgetItem(track.name)
            item.setData(Qt.UserRole, track)
            item.setText(track.name)
            item.setTextAlignment(Qt.AlignLeft)
            item.setIcon(QIcon(":/icons/add.png"))
            self.track_header[track.name] = item
        return item

    def get_variant_header(self, variant: Variant) -> QTableWidgetItem:
        if item := self.variant_header.get(variant.name) is None:
            item = QTableWidgetItem(variant.name)
            item.setData(Qt.UserRole, variant)
            item.setText(variant.name)
            item.setTextAlignment(Qt.AlignHCenter)
            # item.setIcon(QIcon(":/icons/add.png"))
            self.track_header[variant.name] = item
        return item

    def get_selector_header(self) -> QTableWidgetItem:
        item = QTableWidgetItem("Current variant")
        item.setTextAlignment(Qt.AlignLeft)
        item.setIcon(QIcon(":/icons/add.png"))
        return item

    def get_play_header(self) -> QTableWidgetItem:
        item = QTableWidgetItem("Play variant")
        item.setTextAlignment(Qt.AlignLeft)
        item.setIcon(QIcon(":/icons/play.png"))
        return item

    def get_track(self, item: QTableWidgetItem) -> Track:
        pass

    # fixme move columns
    # TODO drag and drop columns
    # TODO context manu

    def get_widget(self, variant: Variant, variant_item: Optional[VariantItem], cell_mode: CellMode):
        return cell_factory(
            mf=self.mf,
            parent=None,
            project_version=self.project_version,
            variant=variant,
            variant_item=variant_item,
            cell_mode=cell_mode,
        )

    def populate_cell(self, row: int, column: int, widget: QWidget):
        self.table.setCellWidget(row, column, widget)

    def populate_single_variant_selector_cell(self, column: int, variant: Variant):
        widget = self.get_widget(variant=variant, variant_item=None, cell_mode=CellMode.SELECTOR)
        self.check_box_group.addButton(widget.enabled)
        widget.enabled.setChecked(variant.selected)
        self.populate_cell(row=VariantGridRowIndex.SELECTOR, column=column, widget=widget)

    def populate_play_single_variant_cell(self, column: int, variant: Variant):
        widget = self.get_widget(variant=variant, variant_item=None, cell_mode=CellMode.PLAY)
        self.populate_cell(row=VariantGridRowIndex.PLAY, column=column, widget=widget)

    def populate_variant_items(self, variant_index: int, variant: Variant):
        cell_mode = CellMode.SELECTOR | CellMode.PLAY | CellMode.VERSION
        for track_index, variant_item in enumerate(variant.items):
            self.populate_cell(
                row=track_index + VariantGridRowIndex.TRACK_OFFSET,
                column=variant_index,
                widget=self.get_widget(variant=variant, variant_item=variant_item, cell_mode=cell_mode),
            )

    def add_track(self, project_version: ProjectVersion, track: Track):
        if self.project_version == project_version:
            self.table.insertRow(self.table.rowCount())
            inserted_row = self.table.rowCount() - 1
            header = self.get_track_header(track=track)
            self.table.setVerticalHeaderItem(inserted_row, header)

    def insert_variant(self, variant_index: int, variant: Variant):
        self.table.insertColumn(variant_index)
        header = self.get_variant_header(variant=variant)
        self.table.setHorizontalHeaderItem(variant_index, header)
        # if variant.type == VariantType.SINGLE:
        self.populate_single_variant_selector_cell(column=variant_index, variant=variant)
        self.populate_play_single_variant_cell(column=variant_index, variant=variant)
        self.populate_variant_items(variant_index=variant_index, variant=variant)

    def remove_track(self, project_version: ProjectVersion, track: Track):
        pass

    def change_track(self, project_version: ProjectVersion, track: Track):
        pass

    @abstractmethod
    def load_project_version(self, project_version: ProjectVersion):
        self.table.insertRow(VariantGridRowIndex.SELECTOR)
        self.table.setVerticalHeaderItem(VariantGridRowIndex.SELECTOR, self.get_selector_header())
        self.table.insertRow(VariantGridRowIndex.PLAY)
        self.table.setVerticalHeaderItem(VariantGridRowIndex.PLAY, self.get_play_header())
        for track in project_version.tracks:
            self.add_track(project_version=project_version, track=track)

    def load_items(self):
        self.table.clear()
        self.table.setUpdatesEnabled(False)
        self.load_project_version(project_version=self.project_version)
        self.table.setUpdatesEnabled(True)

    def set_updates_enabled(self):
        self.table.setUpdatesEnabled(True)


class SingleVariantGrid(VariantGrid):
    def __init__(self, parent, mf, project_version: ProjectVersion):
        super().__init__(parent=parent, mf=mf, project_version=project_version)
        register_listener(mapping={NotificationMessage.SINGLE_VARIANT_ADDED: self.add_variant})

    def add_variant(self, project_version: ProjectVersion, variant: Variant):
        if self.project_version == project_version and variant.type == VariantType.SINGLE:
            self.insert_variant(variant_index=self.table.columnCount(), variant=variant)

    def load_project_version(self, project_version: ProjectVersion):
        super().load_project_version(project_version=project_version)
        for variant in project_version.variants:
            self.insert_variant(variant_index=self.table.columnCount(), variant=variant)


class CompositionVariantGrid(VariantGrid):
    # def __init__(self, parent, mf, project_version: Composition):
    #     super().__init__(parent=parent, mf=mf, project_version=project_version)

    def load_items(self):
        super().load_items()
        # if not self.project_version.get_loops(LoopType.COMPOSITION):
        #     loops = CompositionLoops(loops=[])
        # else:
        #     loops = CompositionLoops(**self.project_version.get_loops(LoopType.COMPOSITION).dict())
        # self.project_version.loops[LoopType.COMPOSITION] = loops
        self.table.setRowCount(len(self.project_version.tracks))
        self.table.setVerticalHeaderLabels([track.name for track in self.project_version.tracks])
        if self.project_version.compositions:
            for variant_index, variant in enumerate(self.project_version.compositions[0].variants):
                self.insert_variant(variant_index=variant_index, variant=variant)
        self.set_updates_enabled()


class VariantToolbar(QToolBar):
    def __init__(self, variant_grid: VariantGrid):
        super().__init__("Variant grid", variant_grid)
        self.setToolButtonStyle(Qt.ToolButtonIconOnly)
        self.setIconSize(QSize(16, 16))
        self.addAction(variant_grid.mf.menu.actions[MenuAttr.SINGLE_VARIANT_NEW])
