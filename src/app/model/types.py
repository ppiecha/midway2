from __future__ import annotations

from abc import ABC
from dataclasses import dataclass
from enum import Enum
from typing import NewType, Dict, Any, List, NamedTuple, TYPE_CHECKING, Optional, TypeVar, Generic
from uuid import UUID

from PySide6.QtWidgets import QWidget
from pydantic import PositiveInt, confloat, conint, BaseModel
from src.app.utils.exceptions import NoDataFound, TooMany

if TYPE_CHECKING:
    from src.app.model.event import Event


class Midi:
    MIN = 0
    MAX = 127
    MIN_C1 = 12
    MAX_B9 = 119


Bpm = PositiveInt
Unit = confloat(ge=0)
Channel = conint(ge=0, le=255)
Beat = confloat(ge=0)
Pitch = conint(ge=Midi.MIN_C1, le=Midi.MAX_B9)
MidiValue = NewType("MidiValue", conint(ge=Midi.MIN, le=Midi.MAX))
MidiBankValue = NewType("MidiValue", conint(ge=Midi.MIN, le=Midi.MAX + 1))
Bend = conint(ge=0, lt=16384)
BendNormalized = confloat(ge=-1, le=1)
BendDurationNormalized = confloat(ge=0, le=1)
NumOfBars = PositiveInt
Id = UUID | str


class NoteUnit(float, Enum):
    WHOLE = 1
    HALF = 2
    QUARTER = 4
    EIGHTH = 8
    SIXTEENTH = 16
    THIRTY_SECOND = 32
    SIXTY_FOURTH = 64
    HUNDRED_TWENTY_EIGHTH = 128


Json = Dict[str, Any]


@dataclass
class DictDiff:
    d1: Dict
    d2: Dict
    diff: List


def dict_diff(d1: Dict, d2: Dict):
    for d1_item in d1.items():
        if d1_item not in d2.items():
            yield d1_item
    for d2_item in d2.items():
        if d2_item not in d1.items():
            yield d2_item


def get_one(data: List, raise_on_empty: bool = False, raise_on_multiple: bool = True):
    if not data and raise_on_empty:
        raise NoDataFound("List is empty on None. Expected exactly one element")
    if raise_on_multiple and len(data) > 1:
        raise TooMany(f"Found more than one element {data}. Expecting exactly one")
    return data[0] if data else None


class TrackType(str, Enum):
    VOICE = "voice"
    RHYTHM = "rhythm"


class TimedEvent(NamedTuple):
    time: int
    event: Event


class Preset(BaseModel):
    sf_name: str
    bank: MidiBankValue
    patch: MidiValue

    def __eq__(self, other: Preset):
        return self.sf_name == other.sf_name and self.bank == other.bank and self.patch == other.patch


class ABCWidgetFinalMeta(type(QWidget), type(ABC)):
    pass


T = TypeVar("T")


@dataclass(eq=True, frozen=True, match_args=True, kw_only=True, slots=True)
class Result(Generic[T]):
    error: Optional[str] = None
    value: Optional[T] = None
