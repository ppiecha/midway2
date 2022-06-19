from __future__ import annotations

import logging
from math import modf, copysign
from typing import Optional, List, Type

from PySide6.QtCore import QRectF, QPointF
from PySide6.QtGui import Qt, QMouseEvent
from PySide6.QtWidgets import QGraphicsScene, QGraphicsSceneMouseEvent, QBoxLayout
from pubsub import pub
from pydantic import NonNegativeInt, PositiveInt

from src.app.backend.synth import Synth
from src.app.gui.editor.key import BlackPianoKey
from src.app.gui.editor.keyboard import KeyboardView
from src.app.gui.editor.node import NoteNode, MetaNode, Node
from src.app.gui.editor.selection import GridSelection
from src.app.gui.widgets import GraphicsView, Box
from src.app.model.event import Event, EventType, Diff, EventDiff
from src.app.model.meter import invert
from src.app.model.midi_keyboard import BaseKeyboard
from src.app.model.sequence import Sequence
from src.app.model.track import TrackVersion
from src.app.model.types import Channel
from src.app.utils.logger import get_console_logger
from src.app.utils.properties import GuiAttr, KeyAttr, NotificationMessage, GridAttr, MidiAttr

logger = get_console_logger(name=__name__, log_level=logging.DEBUG)


class KeyboardGridBox(Box):
    def __init__(self, components: List):
        super().__init__(direction=QBoxLayout.LeftToRight)
        for component in components:
            self.addWidget(component)


class BaseGridView(GraphicsView):
    def __init__(
        self,
        cls: Type[BaseGridScene],
        num_of_bars: PositiveInt,
        channel: Channel,
        synth: Synth,
        track_version: TrackVersion,
    ):
        super().__init__(show_scrollbars=GridAttr.SHOW_SCROLLBARS in cls.GRID_ATTR)
        self._num_of_bars = num_of_bars
        self.grid_scene = cls(num_of_bars=num_of_bars, channel=channel, grid_view=self)
        self.setScene(self.grid_scene)
        if GridAttr.FIXED_HEIGHT in cls.GRID_ATTR:
            self.setFixedHeight(self.sceneRect().height())
        self.keyboard_view = KeyboardView(
            cls=cls.KEYBOARD_CLS,
            synth=synth,
            channel=channel,
            callback=self.mark,
            track_version=track_version,
        )

    @property
    def num_of_bars(self) -> int:
        return self.grid_scene.num_of_bars

    @num_of_bars.setter
    def num_of_bars(self, value) -> None:
        self.grid_scene.num_of_bars = value
        self.setScene(self.grid_scene)
        if GridAttr.FIXED_HEIGHT in self.grid_scene.__class__.GRID_ATTR:
            self.setFixedHeight(self.sceneRect().height())

    def mark(self, show: bool, y: int):
        if show:
            self.grid_scene.selection.show_marker_at_pos(y=y)
        else:
            self.grid_scene.selection.remove_marker()

    def leaveEvent(self, event):
        super().leaveEvent(event)
        self.grid_scene.selection.remove_marker()
        self.keyboard_view.keyboard.deactivate_all()

    def mousePressEvent(self, e: QMouseEvent):
        if (
            self.grid_scene.nodes(pos=self.mapToScene(e.pos()))  # item under cursor
            or not self.grid_scene.selected_nodes()  # no selected items
        ):
            super().mousePressEvent(e)
        else:
            self.grid_scene.select_all(selected=False)


class BaseGridScene(QGraphicsScene):
    KEYBOARD_CLS = None
    GRID_ATTR = GridAttr.DIRECT_SELECTION | GridAttr.MOVE_HORIZONTAL

    def __init__(
        self,
        grid_view: BaseGridView,
        channel: Channel,
        num_of_bars: PositiveInt,
        numerator: int = 4,
        denominator: int = 4,
        grid_divider=GuiAttr.GRID_DIV_UNIT,
    ):
        super().__init__()
        self.grid_view = grid_view
        self.supported_event_types = []
        self._channel = channel
        self._numerator = numerator
        self._denominator = denominator
        self._grid_divider = grid_divider
        self._sequence = None  # Sequence.from_num_of_bars(num_of_bars=num_of_bars)
        self._num_of_bars = num_of_bars
        self.redraw()
        self.selection = GridSelection(grid=self, grid_attr=BaseGridScene.GRID_ATTR)
        self.register_listeners()

    def register_listeners(self):
        if not pub.subscribe(self.add_node, NotificationMessage.EVENT_ADDED):
            raise Exception(f"Cannot register listener {NotificationMessage.EVENT_ADDED}")
        if not pub.subscribe(self.remove_node, NotificationMessage.EVENT_REMOVED):
            raise Exception(f"Cannot register listener {NotificationMessage.EVENT_REMOVED}")

    def ratio(self, x: float) -> float:
        return x / self.bar_width

    def round_to_cell(self, x: float) -> float:
        min_unit_width = self.get_unit_width(unit=GuiAttr.GRID_MIN_UNIT)
        return (x // min_unit_width) * min_unit_width

    def round_to_grid_line(self, x: float) -> float:
        div_unit_width = self.get_unit_width(unit=GuiAttr.GRID_DIV_UNIT)
        return (x // div_unit_width) * div_unit_width

    def set_event_position(self, event: Event, node: Node, x: int, user_defined: bool = False) -> Event:
        if node:
            event.bar_num = node.event.bar_num
            event.beat = node.event.beat
        else:
            if user_defined:
                x = self.round_to_grid_line(x)
            else:
                x = self.round_to_cell(x)
            beat_ratio, bar_num = modf(self.ratio(x))
            beat = self.sequence.meter().unit_from_ratio(ratio=beat_ratio)
            event.bar_num = int(bar_num)
            event.beat = beat
        return event

    def set_event_unit(self, event: Event, node: Node) -> Event:
        if node:
            event.unit = node.event.unit
        else:
            event.unit = GuiAttr.GRID_DIV_UNIT
        return event

    def set_event_pitch(self, node: Node, y: int) -> Event:
        if node:
            if node.event.type != EventType.NOTE:
                raise ValueError("Cannot set pitch for event which is not note")
            return node.event
        key = self.keyboard.get_key_by_pos(position=y)
        return key.event() if key else None

    def point_to_event_diff(
        self,
        e: QGraphicsSceneMouseEvent,
        node: Node = None,
        moving: bool = False,
        resizing: bool = False,
        user_defined: bool = False,
    ) -> Optional[EventDiff]:
        meter = self.sequence.meter()
        x, y = e.scenePos().x(), e.scenePos().y()
        event = self.set_event_pitch(node=node, y=y)
        if event:
            event = self.set_event_position(event=event, node=node, x=x, user_defined=user_defined)
            event = self.set_event_unit(event=event, node=node)
            diff = Diff()
            if moving:
                center = node.scenePos().x() + node.rect.width() / 2
                dist = x - center
                beat_diff_ratio, _ = modf(self.ratio(dist))
                diff.beat_diff = meter.unit_from_ratio(ratio=beat_diff_ratio)
                key = self.keyboard.get_key_by_pos(position=y)
                diff.pitch_diff = int(key.event()) - int(event) if key else None
            elif resizing:
                if not node:
                    raise ValueError("Cannot resize when node is undefined")
                node_right = node.mapToScene(node.rect.topRight())
                min_unit_width = self.get_unit_width(unit=GuiAttr.GRID_MIN_UNIT)
                unit_diff = x - node_right.x()
                if abs(unit_diff) >= min_unit_width:
                    unit_ratio = self.ratio(copysign(min_unit_width, unit_diff))
                    unit_diff = meter.unit_from_ratio(ratio=unit_ratio)
                    if meter.significant_value(unit=meter.add(value=event.unit, value_diff=unit_diff)):
                        diff.unit_diff = unit_diff
            return EventDiff(event=event, diff=diff)
        return None

    def point_to_event(
        self,
        e: QGraphicsSceneMouseEvent,
        node: Node = None,
        moving: bool = False,
        resizing: bool = False,
        user_defined: bool = False,
    ) -> Optional[Event]:
        event_diff = self.point_to_event_diff(
            e=e, node=node, moving=moving, resizing=resizing, user_defined=user_defined
        )
        return self.sequence.get_changed_event(old_event=event_diff.event, diff=event_diff.diff)

    # def point_to_event(
    #     self,
    #     e: QGraphicsSceneMouseEvent,
    #     node: Node = None,
    #     moving: bool = False,
    #     resizing: bool = False,
    #     user_defined: bool = False,
    # ) -> Optional[Event]:
    #     event_diff = self.point_to_event_diff(
    #         e=e,
    #         node=node,
    #         moving=moving,
    #         resizing=resizing,
    #     )
    #     x, y = e.scenePos().x(), e.scenePos().y()
    #     event = self.set_event_pitch(node=node, y=y)
    #     if event:
    #         event = self.set_event_position(
    #             event=event, node=node, x=x, user_defined=user_defined
    #         )
    #         event = self.set_event_unit(event=event, node=node)
    #         new_event = self.sequence.get_moved_event(
    #             old_event=event, event_diff=event_diff
    #         )
    #         return new_event
    #     return None

    def event_to_point(self, event: Event) -> QPointF:
        x = event.bar_num * self.bar_width
        ratio = self.sequence.meter().unit_ratio(unit=event.beat)
        x += ratio * self.bar_width
        x = self.round_to_cell(x)
        key = self.keyboard.get_key_by_event(event=event)
        y = key.key_top
        if isinstance(key, BlackPianoKey):
            y = key.key_top - 4
        return QPointF(x, y)

    def is_matching(self, sequence_id, event_type: EventType):
        return sequence_id == id(self._sequence) and event_type in self.supported_event_types

    def remove_node(self, sequence_id, event: Event):
        if self.is_matching(sequence_id=sequence_id, event_type=event.type):
            found = [node for node in self.nodes() if node.event == event]
            if len(found) == 0:
                raise ValueError(f"Event {event} not found in bar {event.bar_num}")
            logger.debug(f"found events {found}")
            self.delete_nodes(meta_notes=found, hard_delete=True)

    def remove_event(self, event: Event):
        self.sequence.remove_event(bar_num=event.bar_num, event=event)
        logger.debug(self.sequence)

    def _add_node(self, event: Event):
        node = self.node_from_event(event=event)
        logger.debug(f"adding note {node}")
        self.addItem(node)

    def _add_nodes(self, events: List[Event]):
        for event in events:
            self._add_node(event=event)

    def add_node(self, sequence_id, event: Event):
        if self.is_matching(sequence_id=sequence_id, event_type=event.type):
            self._add_node(event=event)

    def add_event(self, event: Event):
        if not self.sequence.has_event(event=event):
            self.sequence.add_event(bar_num=event.bar_num, event=event)
            logger.debug(self.sequence)

    def node_from_event(self, event: Event):
        cls = NoteNode if event.type == EventType.NOTE else MetaNode
        return cls(grid_scene=self, event=event)

    def draw_sequence(self, sequence: Sequence):
        if not sequence:
            return
        self.delete_nodes(meta_notes=self.nodes(), hard_delete=True)
        for _, bar in sequence.bars.items():
            filtered_bar = [e for e in bar if e.type in self.supported_event_types]
            self._add_nodes(events=filtered_bar)

    def delete_node(self, meta_node: Node, hard_delete: bool = True) -> None:
        self.removeItem(meta_node)
        if hard_delete:
            del meta_node

    def delete_nodes(self, meta_notes: List[Node], hard_delete: bool) -> None:
        for meta_note in meta_notes:
            self.delete_node(meta_node=meta_note, hard_delete=hard_delete)

    def nodes(self, rect: QRectF = None, pos: QPointF = None) -> List[Node]:
        if rect:
            return list(filter(lambda item: issubclass(type(item), Node), self.items(rect)))
        if pos:
            return list(filter(lambda item: issubclass(type(item), Node), self.items(pos)))
        return list(filter(lambda item: issubclass(type(item), Node), self.items()))

    def selected_nodes(self, rect: QRectF = None, pos: QPointF = None) -> List[Node]:
        if rect:
            lst = list(filter(lambda node: node.isSelected(), self.nodes(rect)))
        elif pos:
            lst = list(filter(lambda node: node.isSelected(), self.nodes(pos)))
        else:
            lst = list(filter(lambda node: node.isSelected(), self.nodes()))
        return lst

    def not_selected_nodes(self, rect: QRectF = None, pos: QPointF = None) -> List[Node]:
        return [node for node in self.nodes(rect=rect, pos=pos) if node not in self.selected_nodes(rect=rect, pos=pos)]

    def events(self, rect: QRectF = None, pos: QPointF = None) -> List[Event]:
        return [node.event for node in self.nodes(rect=rect, pos=pos)]

    def selected_events(self, rect: QRectF = None, pos: QPointF = None) -> List[Event]:
        return [node.event for node in self.selected_nodes(rect=rect, pos=pos)]

    def not_selected_events(self, rect: QRectF = None, pos: QPointF = None) -> List[Event]:
        return [
            event for event in self.events(rect=rect, pos=pos) if event not in self.selected_events(rect=rect, pos=pos)
        ]

    def set_selected_moving(self, moving: bool = True):
        list(map(lambda node: node.selection.set_moving(moving), self.selected_nodes()))

    def get_unit_width(self, unit: float) -> float:
        return invert(unit) * self.bar_width

    # def set_grid_width_props(self):
    #     self.width_bar = self.grid_divider * KeyAttr.W_HEIGHT
    #     self.width_beat = (self.width_bar / self.numerator) * (self.grid_divider / self.denominator)

    @property
    def numerator(self) -> int:
        return self._numerator

    @numerator.setter
    def numerator(self, value: int) -> None:
        self._numerator = value
        # self.set_grid_width_props()

    @property
    def denominator(self) -> int:
        return self._denominator

    @denominator.setter
    def denominator(self, value: int) -> None:
        self._denominator = value
        # self.set_grid_width_props()

    @property
    def num_of_bars(self) -> int:
        return self._num_of_bars

    @num_of_bars.setter
    def num_of_bars(self, value) -> None:
        self._num_of_bars = value
        self.redraw()

    def redraw(self):
        self.draw_sequence(self.sequence)

    @property
    def grid_divider(self) -> int:
        return self._grid_divider

    @grid_divider.setter
    def grid_divider(self, value: int) -> None:
        self._grid_divider = value
        # self.set_grid_width_props()

    @property
    def bar_width(self) -> int:
        return self.grid_divider * KeyAttr.W_HEIGHT

    @property
    def sequence(self):
        return self._sequence

    @sequence.setter
    def sequence(self, value: Sequence) -> None:
        if self._sequence != value and len(value.bars) > 0:
            self._sequence = value
            self.draw_sequence(sequence=value)
            # logger.debug(f"{self.__class__.__name__} {id(value)} {value}")

    @property
    def channel(self) -> Channel:
        return self._channel

    @property
    def keyboard(self) -> BaseKeyboard:
        return self.grid_view.keyboard_view.keyboard

    def mousePressEvent(self, e: QGraphicsSceneMouseEvent):
        super().mousePressEvent(e)
        if not e.isAccepted():
            pos = e.scenePos()
            _, y = e.scenePos().x(), e.scenePos().y()
            match e.button():
                case Qt.LeftButton:
                    match e.modifiers():
                        case Qt.ControlModifier:
                            if self.selection._selecting:
                                self.selection.selecting = False
                            self.selection.selecting = True
                            self.selection.start_pos = QPointF(pos)
                        case Qt.ShiftModifier:
                            self.keyboard.get_key_by_pos(y).play_note()
                        case Qt.ShiftModifier | Qt.ControlModifier:
                            raise NotImplementedError
                        case Qt.NoModifier:
                            self.selection.selecting = False
                            key = self.keyboard.get_key_by_pos(position=y)
                            event = self.point_to_event(e=e, user_defined=True)
                            if key and event:
                                self.add_event(event=event)
                                key.play_note_in_thread(secs=MidiAttr.KEY_PLAY_TIME)
                case Qt.RightButton:
                    for meta_node in self.nodes(pos):
                        self.remove_event(event=meta_node.event)

    def mouseReleaseEvent(self, e: QGraphicsSceneMouseEvent):
        super().mouseReleaseEvent(e)
        if self.selection.selecting:
            self.selection.selecting = False

    def mouseDoubleClickEvent(self, event: QGraphicsSceneMouseEvent):
        pass

    def mouseMoveEvent(self, e: QGraphicsSceneMouseEvent):
        # self.grid_view.setUpdatesEnabled(False)
        super().mouseMoveEvent(e)
        # if e.buttons() == Qt.LeftButton and not self.selection.selecting:
        #     # nodes := self.nodes(pos=e.scenePos()
        #     for node in self.selected_nodes:
        #         node.setSelected(True)
        #         self.set_selected_moving()
        #         node.mouseMoveEvent(e=e)
        x, y = e.scenePos().x(), e.scenePos().y()
        self.selection.draw_selection(x=x, y=y)
        # self.grid_view.setUpdatesEnabled(True)

    def select_all(self, selected: bool = True):
        list(map(lambda note: note.setSelected(selected), self.nodes()))

    def invert_selection(self):
        list(map(lambda note: note.setSelected(not note.isSelected()), self.nodes()))
