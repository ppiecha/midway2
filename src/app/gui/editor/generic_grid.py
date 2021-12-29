import logging
from typing import Optional, List

from PySide6.QtCore import QRectF, QPointF
from PySide6.QtWidgets import QGraphicsScene, QGraphicsItemGroup
from pydantic import NonNegativeInt

from src.app.gui.editor.keyboard import KeyboardView
from src.app.gui.editor.node import NoteNode, MetaNode, Node
from src.app.mingus.core import value
from src.app.model.bar import Meter
from src.app.model.event import Event, EventType
from src.app.model.sequence import Sequence
from src.app.model.types import Channel, Int
from src.app.utils.logger import get_console_logger
from src.app.utils.properties import GuiAttr, KeyAttr

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
        self._channel = channel
        self._numerator = numerator
        self._denominator = denominator
        self._grid_divider = grid_divider
        self._width_bar = grid_divider * KeyAttr.W_HEIGHT
        self._width_beat = self._denominator / self._numerator * self._width_bar
        self.min_unit = value.thirty_second
        self.min_unit_width = self.get_unit_width(self.min_unit)
        self._keyboard_view: Optional[KeyboardView] = None
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

    def node_from_event(
        self, event: Event, bar_num: NonNegativeInt, is_temporary: bool = True
    ):
        if event.type == EventType.note:
            return NoteNode(
                channel=self.channel,
                grid_scene=self,
                bar_num=bar_num,
                beat=event.beat,
                key=self.keyboard.get_key_by_pitch(pitch=int(event)),
                unit=event.unit,
                is_temporary=is_temporary,
            )
        elif event.type in (EventType.program, EventType.controls):
            return MetaNode(
                event_type=event.type,
                channel=self.channel,
                grid_scene=self,
                bar_num=bar_num,
                beat=event.beat,
            )
        else:
            raise ValueError(f"Unsupported event type {event.type}")

    def draw_sequence(self, cls):
        self.delete_nodes(meta_notes=self.notes(), hard_delete=False)
        note_seq = {
            k: [item for item in v if isinstance(item, cls)]
            for k, v in self.sequence.bars.items()
        }
        logger.debug(f"Only notes from sequence {note_seq}")
        for bar_num in note_seq.keys():
            for note in note_seq[bar_num]:
                meta_node = Node.from_note(note=note, grid_scene=self, bar_num=bar_num)
                self._add_note(meta_node=meta_node, including_sequence=False)

    def _add_note(self, meta_node: Node, including_sequence: bool):
        self.addItem(meta_node)
        if including_sequence:
            self.sequence.add_event(bar_num=meta_node.bar_num, event=meta_node.event)
            logger.debug(f"Sequence {repr(self.sequence)}")

    def delete_node(self, meta_node: Node, hard_delete: bool) -> None:
        self.removeItem(meta_node)
        if hard_delete:
            del meta_node

    def delete_nodes(self, meta_notes: List[Node], hard_delete: bool) -> None:
        for meta_note in meta_notes:
            self.delete_node(meta_node=meta_note, hard_delete=hard_delete)

    def notes(self, rect: QRectF = None, pos: QPointF = None) -> List[Node]:
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
        self._sequence = value

    @property
    def keyboard_view(self) -> KeyboardView:
        return self._keyboard_view

    @keyboard_view.setter
    def keyboard_view(self, value: KeyboardView) -> None:
        self._keyboard_view = value

    @property
    def keyboard(self):
        return self._keyboard_view.keyboard_scene.keyboard_widget

    @property
    def channel(self) -> Channel:
        return self._channel

    # def mouseMoveEvent(self, e: QGraphicsSceneMouseEvent):
    #     super().mouseMoveEvent(e)