from typing import NewType, List, Tuple

from pydantic import BaseModel, conint

MidiValue = NewType("MidiValue", conint(ge=0, le=127))


class ControlClass(BaseModel):
    name: str
    code: MidiValue


class Control(BaseModel):
    class_: ControlClass
    value: MidiValue


class ControlList(BaseModel):
    __root__: List[Control]

    def clear(self):
        self.__root__ = []

    def add_control(self, control: Control):
        self.__root__.append(control)

    def remove_control_class(self, classes: Tuple):
        self.__root__ = [
            control
            for control in self.__root__
            if not isinstance(control.class_, classes)
        ]


class ModulationWheel(ControlClass):
    name = "Modulation Wheel"
    code: MidiValue = MidiValue(1)


class Volume(ControlClass):
    name = "Volume"
    code: MidiValue = MidiValue(7)


class Pan(ControlClass):
    name = "Pan"
    code: MidiValue = MidiValue(10)


class Expression(ControlClass):
    name = "Expression"
    code: MidiValue = MidiValue(11)


class SustainPedal(ControlClass):
    name = "Sustain Pedal"
    code: MidiValue = MidiValue(64)


class FilterResonance(ControlClass):
    name = "Filter Resonance"
    code: MidiValue = MidiValue(71)


class ReleaseTime(ControlClass):
    name = "Release Time"
    code: MidiValue = MidiValue(72)


class AttackTime(ControlClass):
    name = "Attack Time"
    code: MidiValue = MidiValue(74)


class DecayTime(ControlClass):
    name = "Decay Time"
    code: MidiValue = MidiValue(75)


class VibratoRate(ControlClass):
    name = "Vibrato Rate"
    code: MidiValue = MidiValue(76)


class VibratoDepth(ControlClass):
    name = "Vibrato Depth"
    code: MidiValue = MidiValue(77)


class VibratoDelay(ControlClass):
    name = "Vibrato Delay"
    code: MidiValue = MidiValue(78)


class Reverb(ControlClass):
    name = "Reverb"
    code: MidiValue = MidiValue(91)


class Chorus(ControlClass):
    name = "Chorus"
    code: MidiValue = MidiValue(93)


class LSB(ControlClass):
    name = "LSB"
    code: MidiValue = MidiValue(100)


class MSB(ControlClass):
    name = "MSB"
    code: MidiValue = MidiValue(101)


class AllControllersOff(ControlClass):
    name = "All Controllers Off"
    code: MidiValue = MidiValue(121)


class AllNotesOff(ControlClass):
    name = "All Notes Off"
    code: MidiValue = MidiValue(123)
