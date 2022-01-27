from __future__ import annotations

import logging
from typing import Dict, Union, Optional, List, Any, Tuple

from pubsub import pub
from pydantic import PositiveInt, BaseModel, NonNegativeInt

from src.app.model.bar import Bar
from src.app.model.meter import Meter, invert
from src.app.model.event import Event, EventType, Diff
from src.app.model.midi_keyboard import MidiRange
from src.app.model.types import Unit
from src.app.utils.logger import get_console_logger
from src.app.utils.properties import Notification

logger = get_console_logger(name=__name__, log_level=logging.DEBUG)

_bars = Dict[int, Union[Bar, type(None)]]


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

    def add_event(
        self, bar_num: NonNegativeInt, event: Event, callback: bool = True
    ) -> None:
        if bar_num in self.bars.keys():
            event.parent_id = None
            self.bars[bar_num] += event
            if callback:
                pub.sendMessage(
                    topicName=Notification.EVENT_ADDED.value,
                    sequence_id=id(self),
                    event=event,
                )
        else:
            raise ValueError(
                f"Bar number outside of range {bar_num} -> {self.num_of_bars()}"
            )

    def add_events(self, bar_num: NonNegativeInt, events: List[Event]):
        for event in events:
            self.add_event(bar_num=bar_num, event=event)

    def remove_event(
        self, bar_num: NonNegativeInt, event: Event, callback: bool = True
    ) -> None:
        if bar_num not in self.bars.keys():
            raise ValueError(
                f"Bar number outside of range {bar_num} -> {self.num_of_bars()}"
            )
        self.bars[bar_num].remove_event(event=event)
        if callback:
            pub.sendMessage(
                topicName=Notification.EVENT_REMOVED.value,
                sequence_id=id(self),
                event=event,
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

    def get_changed_event(self, old_event: Event, diff: Diff) -> Event:
        meter = self.meter()
        event = old_event.copy(deep=True)
        event.parent_id = old_event.id()
        # pitch
        if MidiRange.in_range(pitch=event.pitch + diff.pitch_diff):
            event.pitch += diff.pitch_diff
        # beat
        if meter.significant_value(unit=diff.beat_diff):
            moved_beat = meter.add(value=event.beat, value_diff=diff.beat_diff)
            if meter.exceeds_length(unit=moved_beat):
                if old_event.bar_num + 1 < self.num_of_bars():
                    event.bar_num = old_event.bar_num + 1
                    event.beat = meter.bar_remainder(unit=moved_beat)
            elif moved_beat < 0:
                if old_event.bar_num - 1 >= 0:
                    event.bar_num = old_event.bar_num - 1
                    event.beat = meter.bar_remainder(unit=moved_beat)
            else:
                event.bar_num = old_event.bar_num
                event.beat = moved_beat
        # unit
        if meter.significant_value(unit=diff.unit_diff):
            event.unit = meter.add(value=old_event.unit, value_diff=diff.unit_diff)
            # logger.debug(f"resized event {event}")
        return event

    def change_event(self, event: Event, diff: Diff, changed_event: Event) -> Event:
        self.remove_event(bar_num=event.bar_num, event=event, callback=False)
        self.add_event(
            bar_num=changed_event.bar_num, event=changed_event, callback=False
        )
        pub.sendMessage(
            topicName=Notification.EVENT_CHANGED.value,
            event=event,
            changed_event=changed_event,
            diff=diff,
        )
        return changed_event

    def change_events(self, event_pairs: List[Tuple[Event, Event]], diff: Diff):
        for event, changed_event in event_pairs:
            self.change_event(event=event, diff=diff, changed_event=changed_event)

