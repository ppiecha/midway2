from __future__ import annotations
import copy
from typing import List, Union, Optional

from pydantic import BaseModel, PositiveInt, NonNegativeInt, NonNegativeFloat

from src.app.lib4py.logger import get_console_logger
from src.app.model.note import Event, EventType
import logging

logger = get_console_logger(name=__name__, log_level=logging.DEBUG)

_notes = List[Union[Event, type(None)]]


class Bar(BaseModel):
    numerator: PositiveInt = 4
    denominator: PositiveInt = 4
    bar_num: NonNegativeInt
    length: NonNegativeFloat = float(numerator) * (1.0 / float(denominator))
    bar: List[Event] = []

    def clear(self):
        self.bar.clear()

    def add_event(self, event: Event) -> None:
        if event.beat >= self.length:
            raise ValueError(f"Item outside of bar range {event.beat}")
        self.bar.append(event)
        self.bar.sort(key=lambda x: x.beat)

    def add_events(self, events: List[Event]):
        for event in events:
            self.add_event(event=event)

    def event_index(self, event: Event) -> int:
        """Index of note in bar list"""
        return self.bar.index(event)

    def remove_event(self, event: Event) -> None:
        self.bar.remove(event)

    def remove_events(self, events: Optional[List[Event]]) -> None:
        for event in events:
            self.remove_event(event=event)

    def remove_events_by_type(self, event_type: EventType) -> None:
        self.remove_events(
            [event for event in self.bar if event.type == event_type])

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

    def __iter__(self):
        return iter(self.bar)

    def events(self):
        return (event for event in self.bar)

    def __repr__(self) -> str:
        """Enable str() and repr() for Bars."""
        return str(self.bar)

    def __len__(self) -> int:
        """Enable the len() method for Bars."""
        return len(self.bar)
