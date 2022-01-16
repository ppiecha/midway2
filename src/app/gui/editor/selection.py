from typing import Optional

from PySide6.QtCore import QPointF, QRect
from PySide6.QtGui import QPen, QBrush
from PySide6.QtWidgets import QGraphicsRectItem, QGraphicsItemGroup

from src.app.gui.editor.key import BlackPianoKey
from src.app.utils.properties import GridAttr, Color, KeyAttr


class NodeSelection:
    def __init__(self, node):
        self.node = node
        self._copying: bool = False
        self._moving: bool = False
        self._resizing: bool = False

    def set_moving(self):
        self.moving = True

    @property
    def moving(self) -> bool:
        return self._moving

    @moving.setter
    def moving(self, value: bool) -> None:
        if value:
            self.resizing = False
            self.copying = False
        self._moving = value

    @property
    def resizing(self) -> bool:
        return self._resizing

    @resizing.setter
    def resizing(self, value: bool) -> None:
        if value:
            self.moving = False
            self.copying = False
        self._resizing = value

    @property
    def copying(self) -> bool:
        return self._copying

    @copying.setter
    def copying(self, value: bool) -> None:
        if value:
            self.moving = False
            self.resizing = False
            # self.copied_grp = self.grid_scene.createItemGroup(
            #     [node.copy_node() for node in self.grid_scene.selected_notes]
            # )
            # for copied in self.copied_grp.childItems():
            #     self.grid_scene._add_note(
            #         meta_node=copied, including_sequence=not copied.is_temporary
            #     )
            #     logger.debug(f"copied notes {self.copied_grp.childItems()}")
        self._copying = value


class GridSelection:
    def __init__(self, grid, grid_attr: GridAttr):
        self.grid = grid
        self.grid_options = grid_attr
        self._selecting: bool = False
        self.copying: bool = False
        self.start_pos: Optional[QPointF] = None
        self.selection_rect: QGraphicsRectItem() = None
        self.copied_grp: Optional[QGraphicsItemGroup] = None
        self.selected_grp: Optional[QGraphicsItemGroup] = None
        self.marker_rect: Optional[QRect] = None

    @property
    def selecting(self) -> bool:
        return self._selecting

    @selecting.setter
    def selecting(self, value: bool):
        self._selecting = value
        if not value:
            self.remove_selection_rect()

    @property
    def is_copying(self) -> bool:
        return self._is_copying

    @is_copying.setter
    def is_copying(self, value: bool) -> None:
        if value:
            self._is_selecting = False
        elif self.copied_grp:
            for item in self.copied_grp.childItems():
                self.removeItem(item)
            self.destroyItemGroup(self.copied_grp)
            logger.debug("copy grp removed")
        self._is_copying = value

    def remove_selection_rect(self):
        if self.selection_rect:
            self.grid.removeItem(self.selection_rect)
            self.selection_rect = None

    def draw_selection(self, x: int, y: int):
        if self.selecting:
            self.remove_selection_rect()
            self.selection_rect = self.grid.addRect(
                QRect(
                    min(self.start_pos.x(), x),
                    min(self.start_pos.y(), y),
                    abs(self.start_pos.x() - x),
                    abs(self.start_pos.y() - y),
                ),
                QPen(Color.GRID_SELECTION),
                QBrush(Color.GRID_SELECTION),
            )
            list(
                map(
                    lambda n: n.setSelected(True),
                    self.grid.nodes(self.selection_rect.rect()),
                )
            )
        self.remove_marker()
        if 0 < x < self.grid.width() and 0 < y < self.grid.height():
            self.show_marker_at_pos(y=y)

    def remove_marker(self, ):
        if self.grid_options.SHOW_MARKER and self.marker_rect:
            self.grid.removeItem(self.marker_rect)

    def show_marker_at_pos(self, y: int):
        self.remove_marker()
        key = self.grid.keyboard.get_key_by_pos(y)
        if self.grid_options.SHOW_MARKER and key:
            key.set_active()
            y_start = key.key_top
            y_height = key.boundingRect().height()
            self.marker_rect = self.grid.addRect(
                QRect(
                    0, y_start, self.grid.width_bar * self.grid.num_of_bars, y_height
                ),
                QPen(Color.GRID_MARKER),
                QBrush(Color.GRID_MARKER),
            )
