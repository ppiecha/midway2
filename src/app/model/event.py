from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from typing import Optional, List, Tuple

from pydantic import BaseModel, NonNegativeFloat, NonNegativeInt

from src.app.mingus.containers.note import Note
from src.app.model.control import Control, PitchBendChain
from src.app.model.meter import invert
from src.app.model.types import Unit, Channel, Beat, Pitch, MidiValue, MidiBankValue
from src.app.utils.properties import MidiAttr


class Preset(BaseModel):
    sf_name: str
    bank: MidiBankValue
    patch: MidiValue


class EventType(str, Enum):
    NOTE = "3-note"
    PROGRAM = "0-program"
    CONTROLS = "1-controls"
    PITCH_BEND = "2-pitch_end"


class Event(BaseModel):
    type: EventType
    channel: Optional[Channel]
    beat: Optional[Beat]
    pitch: Optional[Pitch]
    unit: Optional[NonNegativeFloat]
    velocity: Optional[MidiValue] = MidiAttr.DEFAULT_VELOCITY
    preset: Optional[Preset]
    controls: Optional[List[Control]]
    pitch_bend_chain: Optional[PitchBendChain]
    active: Optional[bool] = True
    bar_num: Optional[NonNegativeInt]

    class Config:
        extra = "allow"

    def dbg(self) -> str:
        patch = self.preset.patch if self.preset else None
        return f"b:{invert(self.beat)} p:{self.pitch} u:{self.unit} bar:{self.bar_num} patch:{patch}"

    def is_related(self, other) -> bool:
        if hasattr(self, "parent_id") and self.parent_id == id(other):
            return True
        elif hasattr(other, "parent_id") and other.parent_id == id(self):
            return True
        else:
            return False

    def has_conflict(self, other) -> bool:
        if self.is_related(other):
            return False
        if self == other:
            return True
        if self.type == other.type == EventType.NOTE and self.pitch != other.pitch:
            return False
        if self.unit is not None and other.unit is not None:
            return invert(self.beat) < invert(other.beat) < invert(self.beat) + (invert(self.unit)) or invert(
                other.beat
            ) < invert(self.beat) < invert(other.beat) + (invert(other.unit))
        else:
            raise ValueError(f"Cannot compare units {self.unit} {other.unit}")

    def is_the_same_note(self, other) -> bool:
        if self.type != EventType.NOTE or self.type != other.type:
            raise ValueError(f"Incorrect type of events {self} {other}")
        return self.pitch == other.pitch

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
            self.type == other.type
            and self.channel == other.channel
            and self.beat == other.beat
            and (self.type != EventType.NOTE or (self.type == EventType.NOTE and self.pitch == other.pitch))
            and self.unit == other.unit
        )

    def __int__(self) -> int:
        if not hasattr(self, "pitch"):
            raise AttributeError(f"Pitch attribute is not defined {str(self)}")
        else:
            return self.pitch

    def note(self) -> Note:
        if self.type != EventType.NOTE:
            raise ValueError(f"Wrong event type {self.type}. It must be a note")
        note = Note().from_int(int(self))
        note.channel = self.channel
        note.velocity = self.velocity
        return note

    @classmethod
    def from_note(cls, note: Note, channel: Channel, beat: Beat, unit: Unit, velocity: MidiValue) -> Event:
        return Event(
            type=EventType.NOTE,
            channel=channel,
            beat=beat,
            unit=unit,
            pitch=int(note),
            velocity=velocity,
        )


PairOfEvents = Tuple[Event, Event]


@dataclass
class Diff:
    beat_diff: Unit = 0
    pitch_diff: int = 0
    unit_diff: Unit = 0


@dataclass
class EventDiff:
    event: Event
    diff: Diff
