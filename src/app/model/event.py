from __future__ import annotations
from enum import Enum
from typing import Optional, NewType, List, Union

from pydantic import BaseModel, conint, confloat, PositiveInt

from src.app.mingus.containers.note import Note
from src.app.utils.constants import DEFAULT_VELOCITY, RULER_HEIGHT, \
    KEY_W_HEIGHT

Int = Union[int, type(None)]
Float = Union[float, type(None)]
Bpm = PositiveInt
Unit = confloat(ge=0)
MidiValue = NewType('MidiValue', conint(ge=0, le=127))
Channel = conint(ge=0, le=255)
Beat = confloat(ge=0)


class LoopType(str, Enum):
    custom = 'custom'
    composition = 'composition'


class Preset(BaseModel):
    sf_name: str
    bank: MidiValue
    patch: MidiValue


class ControlNameCode(BaseModel):
    name: str
    code: MidiValue


class ModulationWheel(ControlNameCode):
    name = 'Modulation Wheel'
    code: MidiValue = MidiValue(1)


class Volume(ControlNameCode):
    name = 'Volume'
    code: MidiValue = MidiValue(7)


class Pan(ControlNameCode):
    name = 'Pan'
    code: MidiValue = MidiValue(10)


class Expression(ControlNameCode):
    name = 'Expression'
    code: MidiValue = MidiValue(11)


class SustainPedal(ControlNameCode):
    name = 'Sustain Pedal'
    code: MidiValue = MidiValue(64)


class FilterResonance(ControlNameCode):
    name = 'Filter Resonance'
    code: MidiValue = MidiValue(71)


class ReleaseTime(ControlNameCode):
    name = 'Release Time'
    code: MidiValue = MidiValue(72)


class AttackTime(ControlNameCode):
    name = 'Attack Time'
    code: MidiValue = MidiValue(74)


class DecayTime(ControlNameCode):
    name = 'Decay Time'
    code: MidiValue = MidiValue(75)


class VibratoRate(ControlNameCode):
    name = 'Vibrato Rate'
    code: MidiValue = MidiValue(76)


class VibratoDepth(ControlNameCode):
    name = 'Vibrato Depth'
    code: MidiValue = MidiValue(77)


class VibratoDelay(ControlNameCode):
    name = 'Vibrato Delay'
    code: MidiValue = MidiValue(78)


class Reverb(ControlNameCode):
    name = 'Reverb'
    code: MidiValue = MidiValue(91)


class Chorus(ControlNameCode):
    name = 'Chorus'
    code: MidiValue = MidiValue(93)


class LSB(ControlNameCode):
    name = 'LSB'
    code: MidiValue = MidiValue(100)


class MSB(ControlNameCode):
    name = 'MSB'
    code: MidiValue = MidiValue(101)


class AllControllersOff(ControlNameCode):
    name = 'All Controllers Off'
    code: MidiValue = MidiValue(121)


class AllNotesOff(ControlNameCode):
    name = 'All Notes Off'
    code: MidiValue = MidiValue(123)


class Control(BaseModel):
    name_code: ControlNameCode
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
    unit: Optional[Unit]
    velocity: Optional[MidiValue]
    preset: Optional[Preset]
    controls: Optional[List[Control]]

    def __int__(self):
        if not hasattr(self, 'pitch'):
            raise AttributeError(f'Pitch attribute is not defined {str(self)}')
        else:
            return self.pitch

    def note(self) -> Note:
        if self.type != EventType.note:
            raise ValueError(f'Wrong event type {self.type}. It must be a note')
        return Note().from_int(int(self))

    @classmethod
    def from_note(cls, note: Note, channel: Channel, beat: Beat,
                  unit: Unit) -> Event:
        return Event(type=EventType.note, channel=channel, beat=beat,
                     unit=unit, pitch=int(note))


KEY_MAPPING = {
    EventType.program: RULER_HEIGHT,
    EventType.controls: RULER_HEIGHT + KEY_W_HEIGHT,
    EventType.pitch_bend: RULER_HEIGHT + 2 * KEY_W_HEIGHT
}