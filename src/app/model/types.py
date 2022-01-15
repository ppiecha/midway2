from enum import Enum
from typing import Union, NewType

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
