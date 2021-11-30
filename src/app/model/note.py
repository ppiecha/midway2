from __future__ import annotations
from enum import Enum
from typing import Optional, NewType, List

from pydantic import BaseModel, conint, confloat


MidiValue = NewType('MidiValue', conint(ge=0, le=127))
Channel = NewType('ChannelValue', conint(ge=0, le=255))
Beat = NewType('Beat', confloat(ge=0))


class Preset(BaseModel):
    sf_name: str
    bank: MidiValue
    patch: MidiValue


class Control(BaseModel):
    name: str
    value: MidiValue


class EventType(str, Enum):
    note = 'note'
    program = 'program'
    controls = 'controls'
    pitch_bend = 'pitch_end'


class Event(BaseModel):
    type: EventType
    channel: Channel
    beat: Beat
    pitch: Optional[MidiValue]
    unit: Optional[confloat(ge=0)]
    velocity: Optional[MidiValue]
    preset: Optional[Preset]
    controls: Optional[List[Control]]

    def __int__(self):
        if not hasattr(self, 'pitch'):
            raise AttributeError(f'Pitch attribute is not defined {str(self)}')
        else:
            return self.pitch
