import copy
from typing import Dict, Union, Optional, List

from pydantic import PositiveInt, BaseModel, NonNegativeInt, validator

from model.bar import Bar
from model.note import Event

_bars = Dict[int, Union[Bar, type(None)]]


class Sequence(BaseModel):
    numerator: PositiveInt = 4
    denominator: PositiveInt = 4
    num_of_bars: PositiveInt
    bars: Dict[NonNegativeInt, Bar] = {}

    @validator('bars', pre=True, always=True)
    def init_bars(cls, v, values):
        for bar_num in range(values['num_of_bars']):
            v[bar_num] = Bar(numerator=values['numerator'],
                             denominator=values['denominator'],
                             bar_num=bar_num)
        return v

    def clear(self):
        for bar_num in self.bars.keys():
            self.bars[bar_num] = Bar(numerator=self.numerator,
                                     denominator=self.denominator,
                                     bar_num=bar_num)

    def clear_bar(self, bar_num: NonNegativeInt):
        self.bars[bar_num] = Bar(numerator=self.numerator,
                                 denominator=self.denominator, bar_num=bar_num)

    def set_num_of_bars(self, value):
        if value < self.num_of_bars:
            for bar_num in range(self.num_of_bars):
                if bar_num > value:
                    del self.bars[bar_num]
        if value > self.num_of_bars:
            for bar_num in range(self.num_of_bars, value):
                self.bars[bar_num] = Bar(numerator=self.numerator,
                                         denominator=self.denominator,
                                         bar_num=bar_num)
        self.num_of_bars = value

    def __getitem__(self, index):
        """Enable the  '[]' notation on Bars to get the item at the index."""
        if index not in self.bars.keys():
            raise ValueError(f"Bar index out of range {index} -> {self.bars}")
        return self.bars[index]

    def events(self):
        return (event for bar_num, bar in self.bars.items() for event in
                bar.events())

    def __len__(self):
        """Enable the len() method for Bars."""
        return self.num_of_bars

    def event_index(self, bar_num: NonNegativeInt, event: Event) -> int:
        if bar_num in self.bars.keys():
            return self.bars[bar_num].event_index(event=event)
        else:
            raise ValueError(
                f"Bar number outside of range {bar_num} -> {self.num_of_bars}")

    def add_event(self, bar_num: NonNegativeInt, event: Event) -> None:
        if bar_num in self.bars.keys():
            self.bars[bar_num] += event
        else:
            raise ValueError(
                f"Bar number outside of range {bar_num} -> {self.num_of_bars}")

    def remove_event(self, bar_num: NonNegativeInt, event: Event) -> None:
        if bar_num not in self.bars.keys():
            raise ValueError(
                f"Bar number outside of range {bar_num} -> {self.num_of_bars}")
        self.bars[bar_num].remove_event(event=event)

    def remove_events(self, bar_num: NonNegativeInt,
                      events: Optional[List[Event]]) -> None:
        for event in events:
            self.remove_event(bar_num=bar_num, event=event)

    def add(self, this, other):
        if isinstance(other, Sequence):
            if other.num_of_bars != this.num_of_bars:
                raise ValueError(
                    f"Sequence has different number of bars {this.num_of_bars} -> {other.num_of_bars}")
            else:
                for bar_num in this.keys():
                    this.bars[bar_num] += other.bars[bar_num]
        elif isinstance(other, Bar):
            if not other.bar_num:
                raise ValueError(f"Bar number not defined {vars(other)}")
            else:
                if other.bar_num in this.bars.keys():
                    this.bars[other.bar_num] += other
                else:
                    raise ValueError(f"Incorrect bar number {other.bar_num}")
        else:
            raise ValueError(f"Unsupported type {type(other)}")

    def __add__(self, other):
        sequence = copy.deepcopy(self)
        return self.add(this=sequence, other=other)

    def __iadd__(self, other):
        return self.add(this=self, other=other)

    def __setitem__(self, index, value):
        """Enable the use of [] = notation on Sequence"""
        if isinstance(value, Bar):
            self.bars[index] = value
        else:
            raise ValueError(
                f"Unsupported type in sequence setter {type(value)}")

    def __repr__(self):
        return str(self.bars)
