import logging
from typing import Optional, List

from PySide6.QtCore import QRectF, QPointF
from PySide6.QtGui import Qt
from PySide6.QtWidgets import QGraphicsScene, QGraphicsSceneMouseEvent
from pubsub import pub
from pydantic import NonNegativeInt

from src.app.gui.editor.node import NoteNode, MetaNode, Node
from src.app.gui.editor.selection import GridSelection
from src.app.mingus.core import value
from src.app.model.bar import Bar
from src.app.model.event import Event, EventType
from src.app.model.sequence import Sequence, BarNumEvent
from src.app.model.types import Channel, Int, NoteUnit
from src.app.utils.logger import get_console_logger
from src.app.utils.properties import GuiAttr, KeyAttr, Notification, GridAttr, MidiAttr
from src.app.utils.units import pos2bar_beat, round2cell

logger = get_console_logger(name=__name__, log_level=logging.DEBUG)


class GenericGridView:
    @property
    def num_of_bars(self) -> int:
        attr_name = "grid_scene"
        if not hasattr(self, attr_name):
            raise ValueError(f"{type(self)} does not have {attr_name} attribute")
        attr_name = "num_of_bars"
        if not hasattr(self.grid_scene, attr_name):
            raise ValueError(
                f"{type(self.grid_scene)} does not have {attr_name} " f"attribute"
            )
        return self.grid_scene.num_of_bars

    @num_of_bars.setter
    def num_of_bars(self, value) -> None:
        self.grid_scene.num_of_bars = value
        self.setScene(self.grid_scene)
        if hasattr(self, "grid_view"):
            self.setFixedHeight(self.sceneRect().height())


class GenericGridScene(QGraphicsScene):
    def __init__(
        self,
        channel: Channel,
        num_of_bars: NonNegativeInt,
        numerator: int = 4,
        denominator: int = 4,
        grid_divider=GuiAttr.GRID_DIV_UNIT,
        grid_attr: GridAttr = GridAttr.selection_direct | GridAttr.move_horizontal,
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
        self._num_of_bars = num_of_bars
        self.redraw()
        self.grid_attr = grid_attr
        self.selection = GridSelection(grid=self, grid_attr=grid_attr)
        self.register_listeners()

    def register_listeners(self):
        if not pub.subscribe(self.add_node, Notification.EVENT_ADDED.value):
            raise Exception(f"Cannot register listener {Notification.EVENT_ADDED}")
        if not pub.subscribe(self.remove_node, Notification.EVENT_REMOVED.value):
            raise Exception(f"Cannot register listener {Notification.EVENT_REMOVED}")

    def point_to_bar_event(
        self, x: int, y: int, unit=NoteUnit.EIGHTH
    ) -> Optional[BarNumEvent]:
        key = self.keyboard.get_key_by_pos(position=y)
        if key:
            bar, beat = pos2bar_beat(
                pos=round2cell(pos=x, cell_width=KeyAttr.W_HEIGHT),
                cell_unit=GuiAttr.GRID_DIV_UNIT,
                cell_width=KeyAttr.W_HEIGHT,
            )
            event = key.event.copy(deep=True)
            Sequence.set_events_attr(
                events=[event],
                attr_val_map={"beat": beat, "unit": unit},
            )
            return BarNumEvent(bar_num=bar, event=event)
        else:
            return None

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
            self.sequence.add_event(event=event)
            logger.debug(self.sequence)

    def node_from_event(self, event: Event):
        cls = NoteNode if event.type == EventType.NOTE else MetaNode
        return cls(grid_scene=self, event=event)

    def draw_sequence(self, sequence: Sequence):
        if not sequence:
            logger.warning(f"Empty sequence. Nothing to draw. Returning...")
            return
        self.delete_nodes(meta_notes=self.nodes(), hard_delete=True)
        for bar_num, bar in sequence.bars.items():
            filtered_bar = Bar(
                meter=sequence.meter(),
                bar_num=bar_num,
                bar=list(filter(lambda e: e.type in self.supported_event_types, bar)),
            )
            # if not filtered_bar.is_empty():
            #     logger.debug(f"draw bar {filtered_bar}")
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

    def set_selected_moving(self):
        list(map(lambda node: node.selection.set_moving(), self.selected_nodes))

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
        if self._sequence != value and len(value.bars) > 0:
            self._sequence = value
            self.draw_sequence(sequence=value)
            # logger.debug(f"{self.__class__.__name__} {id(value)} {value}")

    @property
    def channel(self) -> Channel:
        return self._channel

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
                            bar_event = self.point_to_bar_event(x=x, y=y)
                            if key:
                                self.add_event(bar_event=bar_event)
                                key.play_note_in_thread(secs=MidiAttr.KEY_PLAY_TIME)
                case Qt.RightButton:
                    for meta_node in self.nodes(pos):
                        self.remove_event(
                            BarNumEvent(
                                bar_num=meta_node.bar_num, event=meta_node.event
                            )
                        )

    def mouseReleaseEvent(self, e: QGraphicsSceneMouseEvent):
        super().mouseReleaseEvent(e)
        if self.selection.selecting:
            self.selection.selecting = False

    def mouseDoubleClickEvent(self, event: QGraphicsSceneMouseEvent):
        pass

    def mouseMoveEvent(self, e: QGraphicsSceneMouseEvent):
        super().mouseMoveEvent(e)
        x, y = e.scenePos().x(), e.scenePos().y()
        self.selection.draw_selection(x=x, y=y)
