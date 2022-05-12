from dataclasses import dataclass
from enum import Enum
from typing import Union, NewType, Dict, Any, List

from pydantic import PositiveInt, confloat, conint


class Midi:
    MIN = 0
    MAX = 127
    MIN_C1 = 12
    MAX_B9 = 119


Int = Union[int, type(None)]
Float = Union[float, type(None)]
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
    # print(type(d1.items()))
    # print(tuple(d1.items()))
    # d1_set = set(tuple(d1.items()))
    # d2_set = set(tuple(d2.items()))
    # return d1_set.symmetric_difference(d2_set)
    for d1_item in d1.items():
        if d1_item not in d2.items():
            yield d1_item
    for d2_item in d2.items():
        if d2_item not in d1.items():
            yield d2_item
