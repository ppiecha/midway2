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
from src.app.model.composition import Composition
from src.app.model.loop import (
    Loop,
    CustomLoops,
    CompositionLoops,
    TrackLoopItem,
    LoopType,
)
from src.app.utils.properties import GuiAttr


class FinalMeta(type(QWidget), type(ABC)):
    pass


class LoopGrid(QWidget, ABC, metaclass=FinalMeta):
    def __init__(self, parent, mf, composition: Composition):
        super().__init__(parent)
        self.mf = mf
        self.composition = composition
        self.table = QTableWidget(self)
        # self.table.setAlternatingRowColors(True)
        self.check_box_group = QButtonGroup(self.table)
        self.load_loops()
        self.table.resizeColumnsToContents()
        # self.table.resizeRowsToContents()
        vertical_header = self.table.verticalHeader()
        vertical_header.setSectionResizeMode(QHeaderView.Fixed)
        vertical_header.setDefaultSectionSize(20)
        self.tool_bar = LoopToolbar(loop_grid=self.table)
        self.main_box = Box(direction=QBoxLayout.TopToBottom)
        self.main_box.setContentsMargins(5, 5, 5, 5)
        self.main_box.addWidget(self.tool_bar)
        self.main_box.addWidget(self.table)
        self.setLayout(self.main_box)

    def get_default_loop(self) -> Loop:
        loop = {"name": GuiAttr.DEFAULT, "tracks": [], "checked": True}
        for track in self.composition.tracks:
            loop["tracks"].append(
                TrackLoopItem(
                    loop_track=track,
                    loop_track_version=track.get_default_version().version_name,
                    loop_track_enabled=True,
                )
            )
        return Loop(**loop)

    def get_single_track_loop(self) -> Loop:
        loop = {"name": GuiAttr.SINGLE_TRACK, "tracks": [], "checked": False}
        for track in self.composition.tracks:
            loop["tracks"].append(
                TrackLoopItem(
                    loop_track=track,
                    loop_track_version=track.get_default_version().version_name,
                    loop_track_enabled=False,
                )
            )
        return Loop(**loop)

    def insert_loop(self, loop_index: int, loop: Loop, grid_type: LoopType):
        self.table.setColumnCount(loop_index + 1)
        item = QTableWidgetItem(loop.name)
        self.table.setHorizontalHeaderItem(loop_index, item)
        if grid_type == LoopType.custom:
            widget = TrackVersionBox(
                parent=None,
                composition=self.composition,
                loop=loop,
                loop_item=None,
                show_check_box=True,
                show_combo=False,
            )
            self.check_box_group.addButton(widget.enabled)
            widget.enabled.setChecked(loop.checked)
            self.table.setCellWidget(0, loop_index, widget)
        for track_index, loop_item in enumerate(loop.tracks):
            self.table.setCellWidget(
                track_index + 1,
                loop_index,
                TrackVersionBox(
                    parent=None,
                    composition=self.composition,
                    loop=loop,
                    loop_item=loop_item,
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


class LoopToolbar(QToolBar):
    def __init__(self, loop_grid: QTableWidget):
        super().__init__("Loop grid", loop_grid)
        self.setToolButtonStyle(Qt.ToolButtonIconOnly)
        self.setIconSize(QSize(16, 16))
        a_add_loop = Action(
            mf=loop_grid,
            caption="Add track",
            icon=QIcon(":/icons/add.png"),
            shortcut=None,
            slot=None,
            tip="Add new loop",
            status_tip="Add new loop",
        )
        self.addAction(a_add_loop)


class CustomLoopGrid(LoopGrid):
    def __init__(self, parent, mf, composition: Composition):
        super().__init__(parent=parent, mf=mf, composition=composition)

    def load_loops(self):
        super().load_loops()
        if not self.composition.get_loops(LoopType.custom):
            loops = CustomLoops(
                loops=[self.get_default_loop(), self.get_single_track_loop()]
            )
        else:
            loops = CustomLoops(**self.composition.get_loops(LoopType.custom).dict())
        self.composition.loops[LoopType.custom] = loops
        self.table.setRowCount(len(self.composition.tracks) + 1)
        self.table.setVerticalHeaderLabels(
            ["Current"] + [track.name for track in self.composition.tracks]
        )
        for loop_index, loop in enumerate(loops.loops):
            self.insert_loop(
                loop_index=loop_index, loop=loop, grid_type=LoopType.custom
            )
        self.set_updates_enabled()


class CompositionLoopGrid(LoopGrid):
    def __init__(self, parent, mf, composition: Composition):
        super().__init__(parent=parent, mf=mf, composition=composition)

    def load_loops(self):
        super().load_loops()
        if not self.composition.get_loops(LoopType.composition):
            loops = CompositionLoops(loops=[])
        else:
            loops = CompositionLoops(
                **self.composition.get_loops(LoopType.composition).dict()
            )
        self.composition.loops[LoopType.composition] = loops
        self.table.setRowCount(len(self.composition.tracks))
        self.table.setVerticalHeaderLabels(
            [track.name for track in self.composition.tracks]
        )
        if loops:
            for loop_index, loop in enumerate(loops.loops):
                self.insert_loop(
                    loop_index=loop_index, loop=loop, grid_type=LoopType.composition
                )
        self.set_updates_enabled()
