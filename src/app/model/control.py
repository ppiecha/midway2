from typing import NewType

from pydantic import BaseModel, conint

MidiValue = NewType('MidiValue', conint(ge=0, le=127))


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
