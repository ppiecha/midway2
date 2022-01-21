from __future__ import annotations
import logging
from math import ceil
from typing import Optional, TYPE_CHECKING

from PySide6.QtCore import QRectF, QPoint, Qt
from PySide6.QtGui import QColor, QPainter, QPainterPath, QLinearGradient
from PySide6.QtWidgets import (
    QGraphicsItem,
    QGraphicsSceneMouseEvent,
    QGraphicsSceneHoverEvent,
    QGraphicsItemGroup,
)
from pydantic import NonNegativeFloat

from src.app.gui.editor.selection import NodeSelection
from src.app.utils.properties import Color, KeyAttr, GridAttr

if TYPE_CHECKING:
    from src.app.gui.editor.generic_grid import GenericGridScene
from src.app.gui.editor.key import PianoKey
from src.app.utils.logger import get_console_logger
from src.app.model.event import Event

logger = get_console_logger(name=__name__, log_level=logging.DEBUG)


class Node(QGraphicsItem):
    copied_grp: QGraphicsItemGroup = None

    def __init__(self, grid_scene: GenericGridScene, event: Event):
        super().__init__()
        self.sibling: Optional[Node] = None
        self.selection = NodeSelection(node=self)
        self.grid_attr = grid_scene.GRID_ATTR
        self.setFlag(QGraphicsItem.ItemIsSelectable, True)
        self.setFlag(QGraphicsItem.ItemIsMovable, True)
        self.setFlag(QGraphicsItem.ItemIsFocusable, True)
        self.setFlag(QGraphicsItem.ItemSendsGeometryChanges, True)
        self.setFlag(QGraphicsItem.ItemSendsScenePositionChanges)
        self.setAcceptHoverEvents(True)
        self.grid_scene = grid_scene
        self._event = None
        self.rect = QRectF(0, 0, KeyAttr.W_HEIGHT, KeyAttr.W_HEIGHT)
        self.event = event

    def copy_node(self):
        self.sibling = self.grid_scene.node_from_event(
            event=self.event, bar_num=self.bar_num
        )
        return self.sibling

    # @property
    # def key(self) -> Key:
    #     return self._key
    #
    # @key.setter
    # def key(self, key_: Key):
    #     Sequence.set_events_attr(
    #         events=[self.event],
    #         attr_val_map={
    #             "beat": self.beat,
    #             "unit": self.unit,
    #             "pitch": self.event.pitch,
    #         },
    #     )
    #     self._key = key_
    #     # self.event = Event(
    #     #     pitch=int(key_.note),
    #     #     channel=key_.note.channel,
    #     #     beat=self.beat,
    #     #     unit=self.unit,
    #     # )
    #     self.set_pos()

    @property
    def event(self) -> Event:
        return self._event

    @event.setter
    def event(self, new_event: Event):
        if new_event != self._event:
            point = self.grid_scene.event_to_point(event=new_event)
            self.setPos(point)
            self._event = new_event

    # @property
    # def channel(self) -> Channel:
    #     return self._channel
    #
    # @property
    # def bar_num(self) -> NonNegativeInt:
    #     return self._bar_num
    #
    # @bar_num.setter
    # def bar_num(self, bar: NonNegativeInt) -> None:
    #     self._bar_num = bar
    # self.setPos()

    # @property
    # def beat(self) -> Beat:
    #     return self.event.beat
    #
    # @beat.setter
    # def beat(self, beat: Beat) -> None:
    #     if beat != self.beat:
    #         moved_event = self.grid_scene.sequence.move_event(
    #             BarNumEvent(bar_num=self.bar_num, event=self.event),
    #             beat_diff=beat - self.beat,
    #         )
    #         self.event = moved_event.event
    #         self.set_pos()

    # def set_pos(self):
    #     x = bar_beat2pos(
    #         bar_beat=BarBeat(bar=self.bar_num, beat=self.event.beat),
    #         cell_unit=GuiAttr.GRID_DIV_UNIT,
    #         cell_width=KeyAttr.W_HEIGHT,
    #     )
    #     if isinstance(self.key, PianoKey):
    #         if isinstance(self.key, BlackPianoKey):
    #             y = self.key.black_key_position
    #         else:
    #             y = self.key.position
    #     elif type(self.key) is Key:
    #         y = Key.event_type_to_pos(event_type=self.event.type)
    #     else:
    #         raise ValueError(f"Unknown key type {type(self.key)}")
    #     self.setPos(x, y)

    # @property
    # def bar_event(self) -> BarNumEvent:
    #     return self._bar_event
    #
    # @bar_event.setter
    # def bar_event(self, value: BarNumEvent) -> None:
    #     if value != self.bar_event:
    #         self.grid_scene.sequence.replace_event(old=self.bar_event, new=value)
    #         self._bar_event = value

    def paint(self, painter: QPainter, option, widget=None):
        painter.setPen(QColor(32, 32, 32))
        gradient = QLinearGradient(
            self.boundingRect().topLeft(), self.boundingRect().bottomLeft()
        )
        color: QColor = Color.NODE_START
        if self.isSelected():
            color = Color.NODE_SELECTED
        # elif self.is_temporary:
        #     color = Qt.red  # CLR_NODE_TEMPORARY
        gradient.setColorAt(0.0, color)
        gradient.setColorAt(1.0, Color.NODE_END)
        path = QPainterPath()
        path.addRoundedRect(
            QRectF(
                self.rect.left() + 1,
                self.rect.top() + 1,
                self.rect.width() - 1,
                self.rect.height() - 1,
            ),
            5,
            5,
        )
        painter.fillPath(path, gradient)

    def boundingRect(self):
        return self.rect

    # def itemChange(self, change: QGraphicsItem.GraphicsItemChange, value: Any) -> Any:
    #     # print(change, value)
    #     if change == QGraphicsItem.ItemSelectedChange:
    #         logger.debug(f"{self} selection change {value}")
    #     # elif change == QGraphicsItem.ItemPositionChange:
    #     #     logger.debug(f"{self} position change")
    #     #     # self.grid_scene.move_notes()
    #     #     logger.debug(f"{change}, {value}")
    #     #     print([note for note in self.grid_scene.selected_notes() if note != self])
    #     #     self.grid_scene.move_notes([note for note in self.grid_scene.selected_notes() if note != self],
    #     #                                self.scenePos().x() - value.x(),
    #     #                                self.scenePos().y() - value.y())
    #     # elif QGraphicsItem.ItemScaleHasChanged:
    #     #     logger.debug(f"{change}, {value}")
    #     return super().itemChange(change, value)

    def __repr__(self):
        return str(self.event)

    def mouseMoveEvent(self, e: QGraphicsSceneMouseEvent):
        if self.selection.moving:
            new_event = self.grid_scene.point_to_event(event=e, node=self, unit=self.event.unit)
            if new_event:
                self.grid_scene.sequence.replace_event(
                    old_event=self.event, new_event=new_event
                )
        elif self.selection.resizing:
            pass

    def mouseReleaseEvent(self, e: QGraphicsSceneMouseEvent):
        self.selection.resizing = False
        self.selection.moving = False
        if self.selection.copying:
            self.selection.copying = False

    def mousePressEvent(self, e: QGraphicsSceneMouseEvent):
        if e.button() == Qt.LeftButton:
            match e.modifiers():
                case Qt.ControlModifier if GridAttr.SELECTION_DIRECT in self.grid_attr:
                    self.setSelected(not self.isSelected())
                case Qt.ShiftModifier if GridAttr.copy in self.grid_attr:
                    self.selection.copying = True
                case Qt.NoModifier if self.isSelected():
                    if self.corner_rect().contains(e.pos()):
                        self.selection.resizing = True
                    else:
                        self.grid_scene.set_selected_moving()
            e.accept()
        elif e.button() == Qt.RightButton:
            e.ignore()
            logger.debug("ignored")

    def corner_rect(self):
        return QRectF(self.rect.right() - 3, 0, 3, self.rect.height())

    def hoverMoveEvent(self, e: QGraphicsSceneHoverEvent):
        if GridAttr.RESIZE in self.grid_attr:
            if self.corner_rect().contains(e.pos()) and self.isSelected():
                self.setCursor(Qt.SizeHorCursor)
            else:
                self.unsetCursor()

    def hoverLeaveEvent(self, e: QGraphicsSceneHoverEvent):
        if GridAttr.RESIZE in self.grid_attr:
            self.unsetCursor()


class NoteNode(Node):
    def adjust_size(self, cur_pos: QPoint):
        if self.is_resizing:
            if (
                cur_pos.x() > 0
                and abs(cur_pos.x() - ceil(self.rect.right()))
                >= self.grid_scene.min_unit_width
            ):
                if cur_pos.x() - self.rect.right() > 0:
                    self.resize(diff=self.grid_scene.min_unit_width)
                else:
                    self.resize(diff=-self.grid_scene.min_unit_width)

    def adjust_pos(self, e: QGraphicsSceneMouseEvent):
        def calc_unit(node: Node) -> float:
            unit_ = 0
            center = node.scenePos().x() + node.rect.width() / 2
            dist = e.scenePos().x() - center
            if abs(dist) >= node.grid_scene.min_unit_width:
                unit_ = 1 / node.grid_scene.min_unit
                if dist < 0:
                    unit_ = -unit_

            # center = node.rect.right() / 2
            # diff = (node.scenePos().x() - e.scenePos().x()) // node.grid_scene.min_unit_width
            # print(diff)
            # diff = diff * node.grid_scene.min_unit_width
            # print(diff)
            # x_center = center if node is self else center + diff
            # print(ceil(x_center), x_center, abs(e.pos().x() - ceil(x_center)))
            # if abs(e.pos().x() - ceil(x_center)) >= node.grid_scene.min_unit_width:
            #     if e.pos().x() - ceil(x_center) > 0:
            #         unit_ = 1 / node.grid_scene.min_unit
            #     else:
            #         unit_ = -1 / node.grid_scene.min_unit
            # if unit_ != 0:
            #     logger.debug(f"copy unit {unit_} node {node} {e.pos().x()} - {ceil(x_center)}, {node.rect.right()}")
            #     logger.debug(f"node vars {vars(node)}")
            if unit_ != 0 and not node is self:
                logger.debug(
                    f"center {center} diff {diff} dist {dist} copy {node.is_copying} move {node.is_moving}"
                    f" temp {node.is_temporary} calc unit {unit_}"
                )
                logger.debug(
                    f"note {node} cursor vs copied {e.scenePos().x()} {node.scenePos().x()}"
                )
            return unit_

        if self.is_moving or self.is_copying:
            key_: PianoKey = self.grid_scene.keyboard.get_key_by_pos(e.scenePos().y())
            nodes = (
                self.grid_scene.selected_nodes
                if self.is_moving
                else self.copied_grp.childItems()
            )
            logger.debug(f"notes to move {nodes}")
            self_key = int(self.key.event.note())
            moving_diff = calc_unit(node=self)
            for node in nodes:
                if node.is_temporary:
                    node.move(
                        unit_diff=calc_unit(node=node),
                        key_diff=int(key_.note) - self_key if key_ else 0,
                    )
                else:
                    node.move(
                        unit_diff=moving_diff,
                        key_diff=int(key_.note) - self_key if key_ else 0,
                    )

    def resize(self, diff: float):
        if diff != 0:
            self.prepareGeometryChange()
            if self.rect.right() + diff >= self.grid_scene.min_unit_width:
                self.rect.setRight(self.rect.right() + diff)
                self.unit = self.grid_scene.width_beat / self.rect.width()

    def move(self, unit_diff: float, key_diff: int):
        # notes = []
        # logger.debug(f"moving note {self}, unit_diff {unit_diff}, key_diff {key_diff}")
        if unit_diff != 0 or key_diff != 0:
            if self.is_moving:
                # logger.debug(f"moving note {self}, unit_diff {unit_diff}, key_diff {key_diff}")
                if unit_diff != 0:
                    self.beat = self.beat + unit_diff
                if key_diff != 0:
                    key = self.grid_scene.keyboard.get_key_by_pitch(
                        int(self.key.note) + key_diff
                    )
                    key.event.beat = self.beat
                    self.key = key
            else:
                logger.debug(f"not moved")
            # if self.is_moving:
            #     notes = [note for note in self.grid_scene.selected_notes if note not in (self, self.sibling)]
            # elif self.is_copying:
            #     notes = [note for note in self.copied_grp.childItems() if note not in (self, self.sibling)]
            # if notes:
            #     logger.debug(f"MOVING GROUP {notes}")
            #     self.grid_scene.move_notes(notes=notes, unit_diff=unit_diff, key_diff=key_diff)

    @property
    def unit(self) -> NonNegativeFloat:
        return self.event.unit

    @unit.setter
    def unit(self, unit_: NonNegativeFloat) -> None:
        self.event.unit = unit_
        self.update(self.rect)


class MetaNode(Node):
    def move(self, unit: float):
        if unit != 0:
            self.beat = self.beat + unit

    # def mousePressEvent(self, e: QGraphicsSceneMouseEvent):
    #     if e.button() == Qt.LeftButton:
    #         self.is_moving = True
    #         e.accept()
    #     elif e.button() == Qt.RightButton:
    #         e.ignore()

    def mouseMoveEvent(self, e: QGraphicsSceneMouseEvent):
        if self.is_moving:
            unit = 0
            x_center = self.rect.right() / 2
            if abs(e.pos().x() - ceil(x_center)) >= self.grid_scene.min_unit_width:
                if e.pos().x() - ceil(x_center) > 0:
                    unit = 1 / self.grid_scene.min_unit
                else:
                    unit = -1 / self.grid_scene.min_unit
                logger.debug(
                    f"bar/beat {self.bar_num} {self.beat} {self.grid_scene.sequence} {unit}"
                )
            self.move(unit=unit)

    def mouseReleaseEvent(self, e: QGraphicsSceneMouseEvent):
        logger.debug(f"Meta note mouse release {e.pos()}")
        self.is_moving = False
