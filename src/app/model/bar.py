from __future__ import annotations
import copy
from typing import List, Union, Optional, Iterator

from pydantic import BaseModel, NonNegativeInt, NonNegativeFloat

from src.app.model.meter import Meter, invert
from src.app.utils.exceptions import BeatOutsideOfBar, EventAlreadyExists
from src.app.utils.logger import get_console_logger
from src.app.model.event import Event, EventType
import logging

logger = get_console_logger(name=__name__, log_level=logging.DEBUG)

_notes = List[Union[Event, type(None)]]


class Bar(BaseModel):
    meter: Meter = Meter()
    bar_num: Optional[NonNegativeInt]
    bar: List[Event] = []

    def is_empty(self) -> bool:
        return len(list(self.events())) == 0

    def have_same_beat(self, e1: Event, e2: Event) -> bool:
        if e1.type != e2.type:
            return False
        params = list(filter(lambda x: x.unit is None, [e1, e2]))
        if len(params) == 1:
            raise ValueError(f"Cannot compare units {e1.unit} {e2.unit}")
        if e1.unit:
            return invert(e1.beat) <= invert(e2.beat) < invert(e1.beat) + (
                invert(e1.unit)
            ) or invert(e2.beat) <= invert(e1.beat) < invert(e2.beat) + (
                invert(e2.unit)
            )
        else:
            return e1.beat == e2.beat

    def has_event(self, event: Event) -> bool:
        expr_beat = lambda e: self.have_same_beat(e, event)
        expr_pitch = lambda e: self.have_same_beat(e, event) and e.pitch == event.pitch
        match event.type:
            case EventType.NOTE:
                return len(list(filter(expr_pitch, self.bar))) > 0
            case _:
                return len(list(filter(expr_beat, self.bar))) > 0

    def __eq__(self, other):
        params = list(filter(lambda x: x is None, [self, other]))
        match len(params):
            case 1:
                return False
            case 2:
                return True
        if not isinstance(other, self.__class__):
            raise NotImplementedError
        return (
            self.meter.numerator == other.meter.numerator
            and self.meter.denominator == other.meter.denominator
            and self.bar_num == other.bar_num
            and list(self.events()) == list(other.events())
        )

    def __ne__(self, other):
        return not self == other

    def set_pitch(self):
        pass

    def length(self) -> NonNegativeFloat:
        return self.meter.length()

    def clear(self):
        self.bar.clear()

    def add_event(self, event: Event) -> None:
        if not 0 <= invert(event.beat) < self.length():
            raise BeatOutsideOfBar(
                f"Item outside of bar range 0/{invert(event.beat)}/{self.length()}"
            )
        if self.has_event(event=event):
            raise EventAlreadyExists(f"Event {event} exists in bar {self.bar}")
        self.bar.append(event)
        self.bar.sort(key=lambda e: (e.beat, e.type))

    def add_events(self, events: List[Event]):
        for event in events:
            self.add_event(event=event)

    def event_index(self, event: Event) -> int:
        """Index of note in bar list"""
        return self.bar.index(event)

    def remove_event(self, event: Event) -> None:
        try:
            self.bar.remove(event)
        except ValueError as e:
            raise ValueError(f"Event {event} not found")

    def remove_events(self, events: Optional[List[Event]]) -> None:
        for event in events:
            self.remove_event(event=event)

    def remove_events_by_type(self, event_type: EventType) -> None:
        self.remove_events(list(filter(lambda e: e.type == event_type, self.bar)))

    def add(self, this, other):
        if isinstance(other, Event):
            this.add_event(event=other)
        elif isinstance(other, Bar):
            for event in other:
                this.add_event(event=event)
        elif isinstance(other, List):
            this.add_events(events=other)
        else:
            raise ValueError(f"Unsupported type {type(other)}")
        return this

    def __add__(self, other) -> Bar:
        bar = copy.deepcopy(self)
        return self.add(this=bar, other=other)

    def __iadd__(self, other) -> Bar:
        return self.add(this=self, other=other)

    def __getitem__(self, index) -> Event:
        """Enable the  '[]' notation on Bars to get the item at the index."""
        return self.bar[index]

    def __iter__(self) -> Iterator[Event]:
        return iter(self.bar)

    def events(self):
        return (event for event in self.bar)

    def __repr__(self) -> str:
        """Enable str() and repr() for Bars."""
        return str(self.bar)

    def __len__(self) -> int:
        """Enable the len() method for Bars."""
        return len(self.bar)
