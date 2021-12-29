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
from pydantic import NonNegativeInt

from src.app.utils.properties import Color, KeyAttr, GuiAttr
from src.app.utils.units import bar_beat2pos, BarBeat

if TYPE_CHECKING:
    from src.app.gui.editor.generic_grid import GenericGridScene
from src.app.gui.editor.key import Key, BlackKey
from src.app.utils.logger import get_console_logger
from src.app.mingus.core import value
from src.app.model.event import Event, EventType, KEY_MAPPING
from src.app.model.types import Channel, Beat, NoteUnit

logger = get_console_logger(name=__name__, log_level=logging.DEBUG)


class Node(QGraphicsItem):
    copied_grp: QGraphicsItemGroup = None

    def __init__(
        self,
        channel: Channel,
        grid_scene: GenericGridScene,
        bar_num: NonNegativeInt,
        beat: Beat,
        color: QColor = Color.NODE_START,
        parent=None,
        is_temporary: bool = False,
    ):
        super().__init__(parent=parent)
        self.sibling: Optional[Node] = None
        self.setFlag(QGraphicsItem.ItemIsSelectable, True)
        self.setFlag(QGraphicsItem.ItemIsMovable, True)
        self.setFlag(QGraphicsItem.ItemIsFocusable, True)
        self.setFlag(QGraphicsItem.ItemSendsGeometryChanges, True)
        self.setFlag(QGraphicsItem.ItemSendsScenePositionChanges)
        self.setAcceptHoverEvents(True)
        self.grid_scene = grid_scene
        self.color = color
        self._channel = channel
        self._bar_num: NonNegativeInt = bar_num
        self._beat = beat
        self._event: Optional[Event] = None
        self.is_moving: bool = is_temporary
        self.is_resizing: bool = False
        self.is_temporary: bool = is_temporary
        self.is_copying: bool = False
        self.rect = QRectF(0, 0, KeyAttr.W_HEIGHT, KeyAttr.W_HEIGHT)

    def copy_node(self):
        self.sibling = self.grid_scene.node_from_event(
            event=self.event, bar_num=self.bar_num
        )
        return self.sibling

    def set_moving(self, moving: bool = True) -> None:
        self.is_moving = moving

    @property
    def is_moving(self) -> bool:
        return self._is_moving

    @is_moving.setter
    def is_moving(self, value: bool) -> None:
        if value:
            self.is_resizing = False
            self.is_copying = False
        self._is_moving = value

    @property
    def is_resizing(self) -> bool:
        return self._is_resizing

    @is_resizing.setter
    def is_resizing(self, value: bool) -> None:
        if value:
            self.is_moving = False
            self.is_copying = False
        self._is_resizing = value

    @property
    def is_copying(self) -> bool:
        return self._is_copying

    @is_copying.setter
    def is_copying(self, value: bool) -> None:
        if value:
            self.is_moving = False
            self.is_resizing = False
            self.copied_grp = self.grid_scene.createItemGroup(
                [node.copy_node() for node in self.grid_scene.selected_notes]
            )
            for copied in self.copied_grp.childItems():
                self.grid_scene._add_note(
                    meta_node=copied, including_sequence=not copied.is_temporary
                )
                logger.debug(f"copied notes {self.copied_grp.childItems()}")
        self._is_copying = value

    @property
    def event(self):
        return self._event

    @event.setter
    def event(self, new_event: Event):
        del self.event
        self.grid_scene.sequence.add_event(bar_num=self.bar_num, event=new_event)
        self._event = new_event

    @event.deleter
    def event(self):
        del self._event

    @property
    def channel(self) -> Channel:
        return self._channel

    @property
    def bar_num(self) -> NonNegativeInt:
        return self._bar_num

    @bar_num.setter
    def bar_num(self, bar: NonNegativeInt) -> None:
        self._bar_num = bar
        # self.setPos()

    @property
    def beat(self) -> Beat:
        return self.event.beat

    @beat.setter
    def beat(self, beat: Beat) -> None:
        if beat != self.beat:
            logger.debug(f"MOVING {self}")
            if self.bar_num in self.grid_scene.sequence.bars.keys():
                if beat > 0:
                    if beat >= self.grid_scene.sequence[self.bar_num].length():
                        if self.bar_num < self.grid_scene.num_of_bars - 1:
                            self.grid_scene.sequence.remove_event(
                                bar_num=self.bar_num, event=self.event
                            )
                            self.event.beat = (
                                beat - self.grid_scene.sequence[self.bar_num].length()
                            )
                            self.bar_num += 1
                            self.grid_scene.sequence.add_event(
                                bar_num=self.bar_num, event=self.event
                            )
                    else:
                        self.event.beat = beat
                elif beat == 0:
                    self.event.beat = beat
                elif beat < 0:
                    if self.bar_num > 0:
                        self.grid_scene.sequence.remove_event(
                            bar_num=self.bar_num, event=self.event
                        )
                        self.event.beat = (
                            self.grid_scene.sequence[self.bar_num].length() + beat
                        )
                        self.bar_num -= 1
                        self.grid_scene.sequence.add_event(
                            bar_num=self.bar_num, event=self.event
                        )
            else:
                raise ValueError(
                    f"Bar not in sequence. Sequence {self.grid_scene.sequence}"
                )
            self.set_pos()

    def set_pos(self):
        raise NotImplementedError

    def __del__(self):
        if not self.is_temporary:
            self.grid_scene.sequence.remove_event(
                bar_num=self.bar_num, event=self.event
            )
            logger.debug(
                f"__DEL__ instance of {type(self)} {self} {type(self.event)} {self.event.__repr__()}"
            )
        else:
            logger.debug(
                f"temporary (not deleting) instance of {type(self)} {self} {type(self.event)} {self.event.__repr__()}"
            )

    def paint(self, painter: QPainter, option, widget=None):
        painter.setPen(QColor(32, 32, 32))
        gradient = QLinearGradient(
            self.boundingRect().topLeft(), self.boundingRect().bottomLeft()
        )
        color: QColor = self.color
        if self.isSelected():
            color = Color.NODE_SELECTED
        elif self.is_temporary:
            color = Qt.red  # CLR_NODE_TEMPORARY
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
        temp = "T " if self.is_temporary else ""
        return f"({temp}bar: {str(self.bar_num)}, {repr(self.event)})"


class NoteNode(Node):
    def __init__(
        self,
        channel: Channel,
        grid_scene: GenericGridScene,
        bar_num: NonNegativeInt,
        beat: Beat,
        key: Key,
        unit: float = NoteUnit.EIGHTH,
        color: QColor = Color.NODE_START,
        parent=None,
        is_temporary: bool = False,
    ):
        super().__init__(
            channel=channel,
            grid_scene=grid_scene,
            bar_num=bar_num,
            beat=beat,
            color=color,
            parent=parent,
            is_temporary=is_temporary,
        )
        self._key: Key = key
        # logger.debug(f'NoteNode key {self._key}')
        self._event = Event(
            type=EventType.note,
            pitch=int(key.note),
            channel=key.note.channel,
            beat=beat,
            unit=unit,
        )
        self.set_pos()

    def corner_rect(self):
        return QRectF(self.rect.right() - 3, 0, 3, self.rect.height())

    def mousePressEvent(self, e: QGraphicsSceneMouseEvent):
        logger.debug(f"Node clicked {self}")
        if e.button() == Qt.LeftButton:
            if e.modifiers() == Qt.ControlModifier:
                self.setSelected(not self.isSelected())
            elif e.modifiers() == Qt.ShiftModifier:
                self.is_copying = True
            elif e.modifiers() == Qt.NoModifier:
                if self.isSelected():
                    if self.corner_rect().contains(e.pos()):
                        self.is_resizing = True
                    else:
                        self.grid_scene.set_selected_moving()
            e.accept()
        elif e.button() == Qt.RightButton:
            e.ignore()
            logger.debug("ignored")

    def hoverMoveEvent(self, e: QGraphicsSceneHoverEvent):
        if self.corner_rect().contains(e.pos()) and self.isSelected():
            self.setCursor(Qt.SizeHorCursor)
        else:
            self.unsetCursor()

    def hoverLeaveEvent(self, e: QGraphicsSceneHoverEvent):
        self.unsetCursor()

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
            # print(node is self, self.scenePos(), node.scenePos())
            diff = node.scenePos().x() - self.scenePos().x()

            dist = e.scenePos().x() - center - diff
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
            key_: Key = self.grid_scene.keyboard.get_key_by_pos(e.scenePos().y())
            nodes = (
                self.grid_scene.selected_notes
                if self.is_moving
                else self.copied_grp.childItems()
            )
            logger.debug(f"notes to move {nodes}")
            self_key = int(self.key.note)
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

    def mouseMoveEvent(self, e: QGraphicsSceneMouseEvent):
        self.adjust_size(cur_pos=e.pos())
        self.adjust_pos(e=e)

    def mouseReleaseEvent(self, e: QGraphicsSceneMouseEvent):
        self.is_resizing = False
        self.is_moving = False
        if self.is_copying:
            self.is_copying = False

    def resize(self, diff: float):
        if diff != 0:
            self.prepareGeometryChange()
            if self.rect.right() + diff >= self.grid_scene.min_unit_width:
                self.rect.setRight(self.rect.right() + diff)
                self.unit = self.grid_scene.width_beat / self.rect.width()

    def set_pos(self):
        self.setPos(
            bar_beat2pos(bar_beat=BarBeat(bar=self.bar_num, beat=self.event.beat),
                         cell_unit=GuiAttr.GRID_DIV_UNIT,
                         cell_width=KeyAttr.W_HEIGHT),
            self.key.y_pos_black_key if isinstance(self.key, BlackKey)
            else self.key.y_pos,
        )

    def move(self, unit_diff: float, key_diff: int):
        # notes = []
        # logger.debug(f"moving note {self}, unit_diff {unit_diff}, key_diff {key_diff}")
        if unit_diff != 0 or key_diff != 0:
            if self.is_moving:
                # logger.debug(f"moving note {self}, unit_diff {unit_diff}, key_diff {key_diff}")
                if unit_diff != 0:
                    self.beat = self.beat + unit_diff
                if key_diff != 0:
                    self.key = self.grid_scene.keyboard.get_key_by_pitch(
                        int(self.key.note) + key_diff
                    )
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
    def key(self) -> Key:
        return self._key

    @key.setter
    def key(self, key_: Key):
        self._key = key_
        self.event = Event(
            pitch=int(key_.note),
            channel=key_.note.channel,
            beat=self.beat,
            unit=self.unit,
        )
        self.set_pos()

    @property
    def unit(self) -> float:
        return self.event.unit

    @unit.setter
    def unit(self, unit_: float) -> None:
        self.event.unit = unit_
        self.update(self.rect)


class MetaNode(Node):
    def __init__(
        self,
        event_type: EventType,
        channel: Channel,
        grid_scene,
        bar_num: NonNegativeInt,
        beat: Beat,
        color: QColor = Color.NODE_START,
        parent=None,
    ):
        super().__init__(
            channel=channel,
            grid_scene=grid_scene,
            bar_num=bar_num,
            beat=beat,
            color=color,
            parent=parent,
        )
        self._event = Event(type=event_type, channel=channel, beat=beat)
        self._key: int = KEY_MAPPING[event_type]
        self.set_pos()

    def set_pos(self):
        self.setPos(
            bar_beat2pos(bar_beat=BarBeat(bar=self.bar_num, beat=self.event.beat),
                         cell_unit=GuiAttr.GRID_DIV_UNIT,
                         cell_width=KeyAttr.W_HEIGHT),
            self._key,
        )

    def move(self, unit: float):
        if unit != 0:
            self.beat = self.beat + unit

    def mousePressEvent(self, e: QGraphicsSceneMouseEvent):
        if e.button() == Qt.LeftButton:
            self.is_moving = True
            e.accept()
        elif e.button() == Qt.RightButton:
            e.ignore()

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
