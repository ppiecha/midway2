from enum import Enum
from typing import Union

from pydantic import PositiveInt

Int = Union[int, type(None)]
Float = Union[float, type(None)]
Bpm = PositiveInt


class LoopType(str, Enum):
    custom = 'custom'
    composition = 'composition'
