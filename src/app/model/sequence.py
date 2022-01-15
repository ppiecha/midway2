from __future__ import annotations
import copy
from functools import lru_cache
from math import ceil, copysign
from typing import Dict, Union, Optional, List, Any, NamedTuple

from PySide6.QtCore import QRect, QPoint
from pubsub import pub
from pydantic import PositiveInt, BaseModel, NonNegativeInt

from src.app.model.bar import Bar, Meter
from src.app.model.event import Event, EventType
from src.app.utils.properties import Notification, KeyAttr, GuiAttr
from src.app.utils.units import pos2bar_beat, round2cell

_bars = Dict[int, Union[Bar, type(None)]]


class BarNumEvent(NamedTuple):
    bar_num: NonNegativeInt
    event: Event

    @lru_cache()
    def bar_num_diff(self, x: int) -> int:
        bar, _ = pos2bar_beat(
            pos=round2cell(pos=x, cell_width=KeyAttr.W_HEIGHT),
            cell_unit=GuiAttr.GRID_DIV_UNIT,
            cell_width=KeyAttr.W_HEIGHT,
        )
        return self.bar_num - bar

    @staticmethod
    def unit_diff(x: int, node) -> int:
        min_unit_width = node.grid_scene.min_unit_width
        if x > 0 and abs(x - ceil(node.rect().right())) >= min_unit_width:
            return min_unit_width if x - node.rect().right() > 0 else -min_unit_width
        else:
            return 0

    def pitch_diff(self, y: int, keyboard) -> int:
        if self.event.pitch is None:
            return 0
        if key := keyboard.get_key_by_pos(position=y) is None:
            return 0
        else:
            return self.event.pitch - int(key.note)

    @staticmethod
    def beat_diff(x: int, node) -> int:
        center = node.scenePos().x() + node.rect.width() / 2
        dist = x - center
        if abs(dist) >= node.grid_scene.min_unit_width:
            return int(copysign(1 / node.grid_scene.min_unit, dist))
        else:
            return 0

    def change_valid(self, x: int, y: int, node, keyboard, resizing: bool) -> bool:
        return (
            (self.beat_diff(x, node) != 0 and not resizing)
            or self.pitch_diff(y, keyboard) != 0
            or (self.unit_diff(x, node) != 0 and resizing)
            or self.bar_num_diff(x) != 0
        )

    def get_new_coordinates(
        self, x: int, y: int, node, keyboard, resizing: bool
    ) -> QPoint:
        bar, beat = pos2bar_beat(
            pos=round2cell(pos=x, cell_width=KeyAttr.W_HEIGHT),
            cell_unit=GuiAttr.GRID_DIV_UNIT,
            cell_width=KeyAttr.W_HEIGHT,
        )


class Sequence(BaseModel):
    bars: Dict[NonNegativeInt, Bar] = {}

    def is_empty(self) -> bool:
        for bar in self.bars.values():
            if not bar.is_empty():
                return False
        return True

    def has_event(self, event: Event) -> bool:
        return self.bars[event.bar_num].has_event(event=event)

    def __eq__(self, other):
        params = list(filter(lambda x: x is None, [self, other]))
        match len(params):
            case 1:
                return False
            case 2:
                return True
        if not isinstance(other, self.__class__):
            raise NotImplementedError
        if self.num_of_bars() != other.num_of_bars():
            return False
        for bar_num in self.bars.keys():
            if self.bars[bar_num] != other.bars[bar_num]:
                return False
        return True

    def __ne__(self, other):
        return not self == other

    def meter(self) -> Meter:
        if self.num_of_bars():
            return self.bars[0].meter
        else:
            raise ValueError(f"No bar in the sequence {self!r}")

    def num_of_bars(self) -> PositiveInt:
        return len(self.bars.keys())

    def clear(self):
        meter = self.meter()
        for bar_num in self.bars.keys():
            self.bars[bar_num] = Bar(meter=meter, bar_num=bar_num)

    def clear_bar(self, bar_num: NonNegativeInt):
        self.bars[bar_num] = Bar(meter=self.meter(), bar_num=bar_num)

    def set_num_of_bars(self, value):
        if value <= 0:
            raise ValueError(f"Number of bars {value} cannot be negative or zero")
        if value < self.num_of_bars():
            self.bars = {k: v for k, v in self.bars.items() if k < value}
        else:
            for bar_num in range(self.num_of_bars(), value):
                self.bars[bar_num] = Bar(meter=self.meter(), bar_num=bar_num)

    def __getitem__(self, index):
        """Enable the  '[]' notation on Bars to get the item at the index."""
        if index not in self.bars.keys():
            raise ValueError(f"Bar index out of range {index} -> {self.bars}")
        return self.bars[index]

    def events(self):
        return (event for bar_num, bar in self.bars.items() for event in bar.events())

    def __len__(self):
        """Enable the len() method for Bars."""
        return self.num_of_bars()

    def event_index(self, bar_num: NonNegativeInt, event: Event) -> int:
        if bar_num in self.bars.keys():
            return self.bars[bar_num].event_index(event=event)
        else:
            raise ValueError(
                f"Bar number outside of range {bar_num} -> {self.num_of_bars()}"
            )

    def add_event(self, bar_num: NonNegativeInt, event: Event) -> None:
        if bar_num in self.bars.keys():
            self.bars[bar_num] += event
            pub.sendMessage(
                topicName=Notification.EVENT_ADDED.value,
                sequence_id=id(self),
                bar_event=BarNumEvent(bar_num=bar_num, event=event),
            )
        else:
            raise ValueError(
                f"Bar number outside of range {bar_num} -> {self.num_of_bars()}"
            )

    def add_events(self, bar_num: NonNegativeInt, events: List[Event]):
        for event in events:
            self.add_event(bar_num=bar_num, event=event)

    def remove_event(self, bar_num: NonNegativeInt, event: Event) -> None:
        if bar_num not in self.bars.keys():
            raise ValueError(
                f"Bar number outside of range {bar_num} -> {self.num_of_bars()}"
            )
        self.bars[bar_num].remove_event(event=event)
        pub.sendMessage(
            topicName=Notification.EVENT_REMOVED.value,
            sequence_id=id(self),
            bar_event=BarNumEvent(bar_num=bar_num, event=event),
        )

    def remove_events(
        self, bar_num: NonNegativeInt, events: Optional[List[Event]]
    ) -> None:
        self.bars[bar_num].remove_events(events=events)
        # for event in events:
        #     self.remove_event(bar_num=bar_num, event=event)

    def remove_events_by_type(self, event_type: EventType) -> None:
        for bar in self.bars.values():
            bar.remove_events_by_type(event_type=event_type)

    def add(self, this, other):
        if isinstance(other, Sequence):
            if other.num_of_bars() != this.num_of_bars():
                raise ValueError(
                    f"Sequence has different number of bars {this.num_of_bars()} -> "
                    f"{other.num_of_bars()}"
                )
            else:
                for bar_num in this.bars.keys():
                    this.bars[bar_num] += other.bars[bar_num]
        elif isinstance(other, Bar):
            if other.bar_num is None:
                raise ValueError(f"Bar number not defined {vars(other)}")
            else:
                if other.bar_num in this.bars.keys():
                    this.bars[other.bar_num] += other
                else:
                    this.bars[other.bar_num] = other
        else:
            raise ValueError(f"Unsupported type {type(other)}")
        return this

    def __add__(self, other):
        sequence = self.copy(deep=True)
        return self.add(this=sequence, other=other)

    def __iadd__(self, other):
        return self.add(this=self, other=other)

    def __setitem__(self, index, value):
        """Enable the use of [] = notation on Sequence"""
        if isinstance(value, Bar):
            self.bars[index] = value
        else:
            raise ValueError(f"Unsupported type in sequence setter {type(value)}")

    def __repr__(self):
        return str(self.bars)

    @classmethod
    def from_bars(cls, bars: List[Bar]) -> Sequence:
        sequence = cls(bars={})
        for bar in bars:
            sequence += bar
        return sequence

    @classmethod
    def from_num_of_bars(cls, num_of_bars: PositiveInt, meter: Meter = None):
        if meter is None:
            meter = Meter()
        return cls.from_bars(
            [Bar(meter=meter, bar_num=bar_num) for bar_num in range(num_of_bars)]
        )

    @staticmethod
    def set_events_attr(events: List[Event], attr_val_map: Dict[str, Any]):
        for event in events:
            for attr, value in attr_val_map.items():
                if hasattr(event, attr):
                    setattr(event, attr, value)

    def get_moved_event(
        self, bar_event: BarNumEvent, beat_diff: float, pitch_diff: int
    ) -> BarNumEvent:
        event = bar_event.event.copy(deep=True)
        event.pitch += pitch_diff
        bar_num = bar_event.bar_num
        moved_beat = event.beat + beat_diff
        if moved_beat >= self.bars[bar_event.bar_num].length():
            if bar_num + 1 < self.num_of_bars():
                bar_num += 1
                event.beat = moved_beat - self.bars[bar_event.bar_num].length()
        elif moved_beat < 0:
            if bar_num - 1 >= 0:
                bar_num -= 1
                event.beat = self.bars[bar_event.bar_num].length() + beat_diff
        else:
            event.beat = moved_beat
        return BarNumEvent(bar_num=bar_num, event=event)

    def move_event(
        self, bar_event: BarNumEvent, beat_diff: float = 0.0, pitch_diff: int = 0
    ) -> BarNumEvent:
        moved_event = self.get_moved_event(
            bar_event=bar_event, beat_diff=beat_diff, pitch_diff=pitch_diff
        )
        self.remove_event(bar_num=bar_event.bar_num, event=bar_event.event)
        self.add_event(bar_num=moved_event.bar_num, event=moved_event.event)
        return moved_event

    def replace_event(self, old: BarNumEvent, new: BarNumEvent) -> None:
        self.remove_event(bar_num=old.bar_num, event=old.event)
        self.add_event(bar_num=new.bar_num, event=new.event)
