from abc import ABC, abstractmethod

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
)

from src.app.gui.menu import Action
from src.app.gui.widgets import TrackVersionBox, Box
from src.app.model.project_version import ProjectVersion
from src.app.model.types import ABCWidgetFinalMeta
from src.app.model.variant import Variant, VariantType


class VariantGrid(QWidget, ABC, metaclass=ABCWidgetFinalMeta):
    def __init__(self, parent, mf, project_version: ProjectVersion):
        super().__init__(parent)
        self.mf = mf
        self.project_version = project_version
        self.table = QTableWidget(self)
        # self.table.setAlternatingRowColors(True)
        self.check_box_group = QButtonGroup(self.table)
        self.load_loops()
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

    # def get_default_loop(self) -> Loop:
    #     loop = {"name": GuiAttr.DEFAULT, "tracks": [], "checked": True}
    #     for track in self.project_version.tracks:
    #         loop["tracks"].append(
    #             VariantItem(
    #                 loop_track=track,
    #                 loop_track_version=track.get_default_version().name,
    #                 loop_track_enabled=True,
    #             )
    #         )
    #     return Loop(**loop)
    #
    # def get_single_track_loop(self) -> Loop:
    #     loop = {"name": GuiAttr.SINGLE_TRACK, "tracks": [], "checked": False}
    #     for track in self.project_version.tracks:
    #         loop["tracks"].append(
    #             VariantItem(
    #                 loop_track=track,
    #                 loop_track_version=track.get_default_version().name,
    #                 loop_track_enabled=False,
    #             )
    #         )
    #     return Loop(**loop)

    def insert_loop(self, variant_index: int, variant: Variant):
        self.table.setColumnCount(variant_index + 1)
        item = QTableWidgetItem(variant.name)
        self.table.setHorizontalHeaderItem(variant_index, item)
        if variant.type == VariantType.SINGLE:
            widget = TrackVersionBox(
                parent=None,
                project_version=self.project_version,
                variant=variant,
                variant_item=None,
                show_check_box=True,
                show_combo=False,
            )
            self.check_box_group.addButton(widget.enabled)
            widget.enabled.setChecked(variant.selected)
            self.table.setCellWidget(0, variant_index, widget)
        for track_index, variant_item in enumerate(variant.items):
            self.table.setCellWidget(
                track_index + 1,
                variant_index,
                TrackVersionBox(
                    parent=None,
                    project_version=self.project_version,
                    variant=variant,
                    variant_item=variant_item,
                    show_check_box=True,
                    show_combo=True,
                ),
            )

    @abstractmethod
    def load_loops(self):
        self.table.clear()
        self.table.setUpdatesEnabled(False)

    def set_updates_enabled(self):
        self.table.setUpdatesEnabled(True)


class VariantToolbar(QToolBar):
    def __init__(self, variant_grid: VariantGrid):
        super().__init__("Variant grid", variant_grid)
        self.setToolButtonStyle(Qt.ToolButtonIconOnly)
        self.setIconSize(QSize(16, 16))
        a_add_loop = Action(
            mf=variant_grid.mf,
            caption="Add track",
            icon=QIcon(":/icons/add.png"),
            shortcut=None,
            slot=None,
            tip="Add new loop",
            status_tip="Add new loop",
        )
        self.addAction(a_add_loop)


class SingleVariantGrid(VariantGrid):
    # def __init__(self, parent, mf, project_version: ProjectVersion):
    #     super().__init__(parent=parent, mf=mf, project_version=project_version)

    def load_loops(self):
        super().load_loops()
        # if not self.project_version.get_loops(LoopType.custom):
        #     loops = CustomLoops(loops=[self.get_default_loop(), self.get_single_track_loop()])
        # else:
        #     loops = CustomLoops(**self.project_version.get_loops(LoopType.custom).dict())
        # self.project_version.loops[LoopType.custom] = loops
        self.table.setRowCount(len(self.project_version.tracks) + 1)
        self.table.setVerticalHeaderLabels(["Current"] + [track.name for track in self.project_version.tracks])
        for variant_index, variant in enumerate(self.project_version.variants):
            self.insert_loop(variant_index=variant_index, variant=variant)
        self.set_updates_enabled()


class CompositionVariantGrid(VariantGrid):
    # def __init__(self, parent, mf, project_version: Composition):
    #     super().__init__(parent=parent, mf=mf, project_version=project_version)

    def load_loops(self):
        super().load_loops()
        # if not self.project_version.get_loops(LoopType.COMPOSITION):
        #     loops = CompositionLoops(loops=[])
        # else:
        #     loops = CompositionLoops(**self.project_version.get_loops(LoopType.COMPOSITION).dict())
        # self.project_version.loops[LoopType.COMPOSITION] = loops
        self.table.setRowCount(len(self.project_version.tracks))
        self.table.setVerticalHeaderLabels([track.name for track in self.project_version.tracks])
        if self.project_version.compositions:
            for variant_index, variant in enumerate(self.project_version.compositions[0].variants):
                self.insert_loop(variant_index=variant_index, variant=variant)
        self.set_updates_enabled()
