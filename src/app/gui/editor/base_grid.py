from __future__ import annotations
import logging
from math import modf
from typing import Optional, List, Type

from PySide6.QtCore import QRectF, QPointF
from PySide6.QtGui import Qt, QMouseEvent
from PySide6.QtWidgets import QGraphicsScene, QGraphicsSceneMouseEvent, QBoxLayout
from pubsub import pub
from pydantic import NonNegativeInt

from src.app.backend.synth import Synth
from src.app.gui.editor.key import BlackPianoKey
from src.app.gui.editor.keyboard import KeyboardView
from src.app.gui.editor.node import NoteNode, MetaNode, Node
from src.app.gui.editor.selection import GridSelection
from src.app.gui.widgets import GraphicsView, Box
from src.app.model.bar import Bar
from src.app.model.event import Event, EventType
from src.app.model.meter import invert
from src.app.model.midi_keyboard import BaseKeyboard
from src.app.model.sequence import Sequence
from src.app.model.types import Channel
from src.app.utils.logger import get_console_logger
from src.app.utils.properties import GuiAttr, KeyAttr, Notification, GridAttr, MidiAttr

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
        num_of_bars: int,
        channel: Channel,
        synth: Synth,
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
            or not self.grid_scene.selected_nodes  # no selected items
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
        num_of_bars: NonNegativeInt,
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
        if not pub.subscribe(self.add_node, Notification.EVENT_ADDED.value):
            raise Exception(f"Cannot register listener {Notification.EVENT_ADDED}")
        if not pub.subscribe(self.remove_node, Notification.EVENT_REMOVED.value):
            raise Exception(f"Cannot register listener {Notification.EVENT_REMOVED}")

    def ratio(self, x: float) -> float:
        return x / self.bar_width

    def round_to_cell(self, x: float) -> float:
        min_unit_width = invert(GuiAttr.GRID_MIN_UNIT) * self.bar_width
        return (x // min_unit_width) * min_unit_width

    def round_to_grid_line(self, x: float) -> float:
        div_unit_width = invert(GuiAttr.GRID_DIV_UNIT) * self.bar_width
        return (x // div_unit_width) * div_unit_width

    def set_event_position(
        self, event: Event, node: Node, x: int, user_defined: bool = False
    ) -> Event:
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
            event.bar_num = bar_num
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
                raise ValueError(f"Cannot set pitch for event which is not note")
            return node.event
        else:
            key = self.keyboard.get_key_by_pos(position=y)
            return key.event() if key else None

    def point_to_event(
        self,
        e: QGraphicsSceneMouseEvent,
        node: Node = None,
        moving: bool = False,
        resizing: bool = False,
        user_defined: bool = False,
    ) -> Optional[Event]:
        x, y = e.scenePos().x(), e.scenePos().y()
        event = self.set_event_pitch(node=node, y=y)
        if event:
            event = self.set_event_position(
                event=event, node=node, x=x, user_defined=user_defined
            )
            event = self.set_event_unit(event=event, node=node)
            beat_diff = 0
            pitch_diff = 0
            unit_diff = 0
            if moving:
                center = node.scenePos().x() + node.rect.width() / 2
                dist = x - center
                beat_diff_ratio, _ = modf(self.ratio(dist))
                beat_diff = self.sequence.meter().unit_from_ratio(ratio=beat_diff_ratio)
                key = self.keyboard.get_key_by_pos(position=y)
                pitch_diff = int(key.event()) - int(event) if key else None
            elif resizing:
                if not node:
                    raise ValueError(f"Cannot resize when node is undefined")
                node_right = node.mapToScene(node.rect.topRight())
                unit_ratio = self.ratio(y - node_right.y())
                unit_diff = self.sequence.meter().unit_from_ratio(ratio=unit_ratio)
                logger.debug(
                    f"unit values {y} {node_right.y()} {unit_ratio} {unit_diff}"
                )
            return self.sequence.get_moved_event(
                old_event=event,
                beat_diff=beat_diff,
                pitch_diff=pitch_diff,
                unit_diff=unit_diff,
            )
        else:
            return None

    def event_to_point(self, event: Event) -> QPointF:
        x = event.bar_num * self.bar_width
        ratio = self.sequence.meter().unit_ratio(unit=event.beat)
        x += ratio * self.bar_width
        x = self.round_to_cell(x)
        key = self.keyboard.get_key_by_event(event=event)
        y = key.key_top
        if type(key) is BlackPianoKey:
            y = key.key_top - 4
        return QPointF(x, y)

    def is_matching(self, sequence_id, event_type: EventType):
        return (
            sequence_id == id(self._sequence)
            and event_type in self.supported_event_types
        )

    def remove_node(self, sequence_id, event: Event):
        if self.is_matching(sequence_id=sequence_id, event_type=event.type):
            found = [node for node in self.nodes() if node.event == event]
            if len(found) == 0:
                raise ValueError(f"Event {event} not found in bar {event.bar_num}")
            else:
                self.delete_nodes(meta_notes=found, hard_delete=True)

    def remove_event(self, event: Event):
        self.sequence.remove_event(bar_num=event.bar_num, event=event)
        logger.debug(self.sequence)

    def _add_node(self, event: Event):
        node = self.node_from_event(event=event)
        self.addItem(node)

    def _add_bar(self, bar: Bar):
        for event in bar:
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
        for bar_num, bar in sequence.bars.items():
            filtered_bar = Bar(
                meter=sequence.meter(),
                bar_num=bar_num,
                bar=list(filter(lambda e: e.type in self.supported_event_types, bar)),
            )
            self._add_bar(bar=filtered_bar)

    def delete_node(self, meta_node: Node, hard_delete: bool = True) -> None:
        self.removeItem(meta_node)
        if hard_delete:
            del meta_node

    def delete_nodes(self, meta_notes: List[Node], hard_delete: bool) -> None:
        for meta_note in meta_notes:
            self.delete_node(meta_node=meta_note, hard_delete=hard_delete)

    def nodes(self, rect: QRectF = None, pos: QPointF = None) -> List[Node]:
        if rect:
            return list(
                filter(lambda item: issubclass(type(item), Node), self.items(rect))
            )
        elif pos:
            return list(
                filter(lambda item: issubclass(type(item), Node), self.items(pos))
            )
        else:
            return list(filter(lambda item: issubclass(type(item), Node), self.items()))

    @property
    def selected_nodes(self, rect: QRectF = None, pos: QPointF = None) -> List[Node]:
        lst = []
        if rect:
            lst = list(filter(lambda note: note.isSelected(), self.nodes(rect)))
        elif pos:
            lst = list(filter(lambda note: note.isSelected(), self.nodes(pos)))
        else:
            lst = list(filter(lambda note: note.isSelected(), self.nodes()))
        return lst

    def set_selected_moving(self, moving: bool = True):
        list(map(lambda node: node.selection.set_moving(moving), self.selected_nodes))

    def get_unit_width(self, unit: float) -> float:
        return self.width_bar / unit

    def set_grid_width_props(self):
        self.width_bar = self.grid_divider * KeyAttr.W_HEIGHT
        self.width_beat = (self.width_bar / self.numerator) * (
            self.grid_divider / self.denominator
        )

    @property
    def numerator(self) -> int:
        return self._numerator

    @numerator.setter
    def numerator(self, value: int) -> None:
        self._numerator = value
        self.set_grid_width_props()

    @property
    def denominator(self) -> int:
        return self._denominator

    @denominator.setter
    def denominator(self, value: int) -> None:
        self._denominator = value
        self.set_grid_width_props()

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
        self.set_grid_width_props()

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
            x, y = e.scenePos().x(), e.scenePos().y()
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
                            if key:
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
