from enum import Enum
from typing import Union

from pydantic import PositiveInt, confloat, conint

Int = Union[int, type(None)]
Float = Union[float, type(None)]
Bpm = PositiveInt
Unit = confloat(ge=0)
Channel = conint(ge=0, le=255)
Beat = confloat(ge=0)


class NoteUnit(float, Enum):
    WHOLE = 1
    HALF = 2
    QUARTER = 4
    EIGHTH = 8
    SIXTEENTH = 16
    THIRTY_SECOND = 32
    SIXTY_FOURTH = 64
    HUNDRED_TWENTY_EIGHTH = 128
