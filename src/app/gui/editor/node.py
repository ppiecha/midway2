from __future__ import annotations
import logging
from typing import Optional, TYPE_CHECKING

from PySide6.QtCore import QRectF, Qt
from PySide6.QtGui import QColor, QPainter, QPainterPath, QLinearGradient
from PySide6.QtWidgets import (
    QGraphicsItem,
    QGraphicsSceneMouseEvent,
    QGraphicsSceneHoverEvent,
    QGraphicsItemGroup,
)
from pubsub import pub

from src.app.gui.editor.selection import NodeSelection
from src.app.model.bar import Bar
from src.app.utils.properties import Color, KeyAttr, GridAttr, Notification

if TYPE_CHECKING:
    from src.app.gui.editor.base_grid import BaseGridScene
from src.app.utils.logger import get_console_logger
from src.app.model.event import Event, Diff

logger = get_console_logger(name=__name__, log_level=logging.DEBUG)


class Node(QGraphicsItem):
    copied_grp: QGraphicsItemGroup = None

    def __init__(self, grid_scene: BaseGridScene, event: Event):
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
        self._event: Optional[Event] = None
        self.rect = QRectF(0, 0, KeyAttr.W_HEIGHT, KeyAttr.W_HEIGHT)
        self.event = event
        self.register_listeners()

    def register_listeners(self):
        if not pub.subscribe(self.event_changed, Notification.EVENT_CHANGED.value):
            raise Exception(f"Cannot register listener {Notification.EVENT_CHANGED}")

    def event_changed(self, event: Event, changed_event: Event):
        if id(event) == id(self.event):
            self.event = changed_event

    def copy_node(self):
        self.sibling = self.grid_scene.node_from_event(
            event=self.event, bar_num=self.bar_num
        )
        return self.sibling

    @property
    def event(self) -> Event:
        return self._event

    @event.setter
    def event(self, new_event: Event):
        point = self.grid_scene.event_to_point(event=new_event)
        self.prepareGeometryChange()
        self.setPos(point)
        if self._event is None or (
            self._event is not None and self._event.unit != new_event.unit
        ):
            self.rect.setWidth(self.grid_scene.get_unit_width(new_event.unit))
        self._event = new_event

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

    def __repr__(self):
        return f"{str(self.scenePos())} {str(self.event)}"

    def is_move_allowed(self, old_event: Event, new_event: Event) -> bool:
        if (
            new_event.beat != old_event.beat
            and GridAttr.MOVE_HORIZONTAL not in self.grid_attr
        ):
            return False
        old_key = self.grid_scene.keyboard.get_key_by_event(event=old_event)
        new_key = self.grid_scene.keyboard.get_key_by_event(event=new_event)
        if (
            old_key.key_top != new_key.key_top
            and GridAttr.MOVE_VERTICAL not in self.grid_attr
        ):
            return False
        return True

    def mouseMoveEvent(self, e: QGraphicsSceneMouseEvent):
        sequence = self.grid_scene.sequence
        event_diff = self.grid_scene.point_to_event_diff(
            e=e,
            node=self,
            moving=self.selection.moving,
            resizing=self.selection.resizing,
        )
        if not event_diff:
            return
        old_events = self.grid_scene.selected_events()
        new_events = [
            sequence.get_changed_event(old_event=event, diff=event_diff.diff)
            for event in old_events
        ]
        pairs = list(zip(old_events, new_events))
        if sequence.is_change_valid(event_pairs=pairs) and all(
            [self.is_move_allowed(old, new) for old, new in pairs]
        ):
            count = len(self.grid_scene.nodes())
            sequence.change_events(event_pairs=pairs)
            assert count == len(self.grid_scene.nodes())

    def mouseReleaseEvent(self, e: QGraphicsSceneMouseEvent):
        self.selection.resizing = False
        self.selection.moving = False
        if self.selection.copying:
            self.selection.copying = False

    def mousePressEvent(self, e: QGraphicsSceneMouseEvent):
        if e.button() == Qt.LeftButton:
            match e.modifiers():
                case Qt.ControlModifier if GridAttr.DIRECT_SELECTION in self.grid_attr:
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
    pass


class MetaNode(Node):
    pass
