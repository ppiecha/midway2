import logging
from typing import Optional, List

from PySide6.QtCore import QRectF, QPointF
from PySide6.QtWidgets import QGraphicsScene, QGraphicsItemGroup
from pubsub import pub
from pydantic import NonNegativeInt

from src.app.gui.editor.key import Key
from src.app.gui.editor.node import NoteNode, MetaNode, Node
from src.app.mingus.core import value
from src.app.model.bar import Meter, Bar
from src.app.model.event import Event, EventType
from src.app.model.sequence import Sequence, BarNumEvent
from src.app.model.types import Channel, Int, NoteUnit
from src.app.utils.logger import get_console_logger
from src.app.utils.properties import GuiAttr, KeyAttr, Notification
from src.app.utils.units import pos2bar_beat, round2cell

logger = get_console_logger(name=__name__, log_level=logging.DEBUG)


class GenericGridScene(QGraphicsScene):
    def __init__(
        self,
        channel: Channel,
        numerator: int = 4,
        denominator: int = 4,
        grid_divider=GuiAttr.GRID_DIV_UNIT,
        num_of_bars: Int = None,
    ):
        super().__init__()
        self.supported_event_types = []
        self._channel = channel
        self._numerator = numerator
        self._denominator = denominator
        self._grid_divider = grid_divider
        self._width_bar = grid_divider * KeyAttr.W_HEIGHT
        self._width_beat = self._denominator / self._numerator * self._width_bar
        self.min_unit = value.thirty_second
        self.min_unit_width = self.get_unit_width(self.min_unit)
        self._sequence: Optional[Sequence] = None
        self.num_of_bars = num_of_bars
        self.sequence = Sequence(
            meter=Meter(numerator=self.numerator, denominator=self.denominator),
            num_of_bars=self.num_of_bars,
        )
        self._is_selecting: bool = False
        self._is_copying: bool = False
        self.copied_grp: Optional[QGraphicsItemGroup] = None
        self.selected_grp: Optional[QGraphicsItemGroup] = None
        self.register_listeners()

    def register_listeners(self):
        if not pub.subscribe(self.add_node, Notification.EVENT_ADDED.value):
            raise Exception(f"Cannot register listener {Notification.EVENT_ADDED}")
        if not pub.subscribe(self.remove_node, Notification.EVENT_REMOVED.value):
            raise Exception(f"Cannot register listener {Notification.EVENT_REMOVED}")

    def point_to_bar_event(self, x: int, y: int) -> BarNumEvent:
        key = self.keyboard.get_key_by_pos(position=y)
        bar, beat = pos2bar_beat(
            pos=round2cell(pos=x, cell_width=KeyAttr.W_HEIGHT),
            cell_unit=GuiAttr.GRID_DIV_UNIT,
            cell_width=KeyAttr.W_HEIGHT,
        )
        event = key.event.copy(deep=True)
        Sequence.set_events_attr(
            events=[event],
            attr_val_map={"beat": beat, "unit": NoteUnit.EIGHTH},
        )
        return BarNumEvent(bar_num=bar, event=event)

    def is_matching(self, sequence_id, event_type: EventType):
        return (
            sequence_id == id(self._sequence)
            and event_type in self.supported_event_types
        )

    def remove_node(self, sequence_id, bar_event: BarNumEvent):
        if self.is_matching(sequence_id=sequence_id, event_type=bar_event.event.type):
            found = [node for node in self.nodes() if node.event == bar_event.event]
            if len(found) == 0:
                raise ValueError(
                    f"Event {bar_event.event} not found in bar {bar_event.bar_num}"
                )
            else:
                self.delete_nodes(meta_notes=found, hard_delete=True)

    def remove_event(self, bar_event: BarNumEvent):
        self.sequence.remove_event(bar_num=bar_event.bar_num, event=bar_event.event)
        logger.debug(self.sequence)

    def _add_node(self, bar_event: BarNumEvent, is_temporary: bool = False):
        node = self.node_from_event(
            event=bar_event.event, bar_num=bar_event.bar_num, is_temporary=is_temporary
        )
        self.addItem(node)

    def _add_bar(self, bar: Bar):
        for event in bar:
            self._add_node(bar_event=BarNumEvent(bar_num=bar.bar_num, event=event))

    def add_node(self, sequence_id, bar_event: BarNumEvent):
        if self.is_matching(sequence_id=sequence_id, event_type=bar_event.event.type):
            self._add_node(bar_event=bar_event, is_temporary=False)

    def add_event(self, bar_event: BarNumEvent):
        self.sequence.add_event(bar_num=bar_event.bar_num, event=bar_event.event)
        logger.debug(self.sequence)

    def node_from_event(
        self, event: Event, bar_num: NonNegativeInt, is_temporary: bool
    ):
        match event.type:
            case event_type if event_type == EventType.NOTE:
                return NoteNode(
                    channel=self.channel,
                    grid_scene=self,
                    bar_num=bar_num,
                    beat=event.beat,
                    key=self.keyboard.get_key_by_pitch(pitch=int(event)),
                    unit=event.unit,
                    is_temporary=is_temporary,
                )
            case event_type if event_type in (
                EventType.PROGRAM,
                EventType.CONTROLS,
                EventType.PITCH_BEND,
            ):
                return MetaNode(
                    channel=self.channel,
                    grid_scene=self,
                    bar_num=bar_num,
                    beat=event.beat,
                    key=Key(event_type=event.type, channel=self.channel),
                )
            case _:
                raise ValueError(f"Unsupported event type {event.type}")

    def draw_sequence(self, sequence: Sequence):
        self.delete_nodes(meta_notes=self.nodes(), hard_delete=True)
        for bar_num, bar in sequence.bars.items():
            filtered_bar = Bar(
                meter=sequence.meter(),
                bar_num=bar_num,
                bar=[
                    event for event in bar if event.type in self.supported_event_types
                ],
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

    def get_unit_width(self, unit: float) -> float:
        return self.width_bar / unit

    def set_grid_width_props(self):
        self.width_bar = self.grid_divider * KeyAttr.W_HEIGHT
        self.width_beat = (self.width_bar / self.numerator) * (
            self.grid_divider / self.denominator
        )

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
    def grid_divider(self) -> int:
        return self._grid_divider

    @grid_divider.setter
    def grid_divider(self, value: int) -> None:
        self._grid_divider = value
        self.set_grid_width_props()

    @property
    def width_bar(self) -> int:
        return self._width_bar

    @width_bar.setter
    def width_bar(self, value: int) -> None:
        self._width_bar = value

    @property
    def width_beat(self) -> int:
        return self._width_beat

    @width_beat.setter
    def width_beat(self, value: int) -> None:
        self._width_beat = value

    @property
    def sequence(self):
        return self._sequence

    @sequence.setter
    def sequence(self, value: Sequence) -> None:
        if self._sequence != value:
            self._sequence = value
            self.draw_sequence(sequence=value)
            logger.debug(f"generic grid sequence setter {value}")

    @property
    def channel(self) -> Channel:
        return self._channel

    # def mouseMoveEvent(self, e: QGraphicsSceneMouseEvent):
    #     super().mouseMoveEvent(e)
