from __future__ import annotations

import logging
from enum import Enum
from typing import NewType, List, Tuple, Callable

from pydantic import BaseModel, conint, confloat

from src.app.model.types import Bpm, NoteUnit
from src.app.utils.logger import get_console_logger
from src.app.utils.units import unit2tick, nvn

MidiValue = NewType("MidiValue", conint(ge=0, le=127))
Bend = conint(ge=0, lt=16384)
BendNormalized = confloat(ge=-1, le=1)
BendDurationNormalized = confloat(ge=0, le=1)

logger = get_console_logger(name=__name__, log_level=logging.DEBUG)


class PitchBend(BaseModel):
    time: int
    value: Bend


class PitchBendValues(int, Enum):
    MIN = 0
    NORM = 8192
    MAX = 16384


class PitchBendChain(BaseModel):
    __root__: List[PitchBend]

    @classmethod
    def gen_chain(cls,
                  bend_fun: Callable,
                  bpm: Bpm,
                  duration: NoteUnit = NoteUnit.EIGHTH,
                  start_time: NoteUnit = None,
                  stop_time: NoteUnit = None,
                  ) -> PitchBendChain:
        max_tick = unit2tick(unit=duration, bpm=bpm) + 1
        start_tick = unit2tick(unit=nvn(start_time, 0), bpm=bpm)
        stop_tick = unit2tick(unit=duration - nvn(stop_time, 0), bpm=bpm)
        logger.debug(f"max_tick {max_tick}")
        timeline = [tick for tick in range(max_tick)]
        logger.debug(f"timeline {timeline}")
        timeline_norm = [tick / max_tick for tick in timeline]
        logger.debug(f"timeline_norm {timeline_norm}")
        bend_values_norm = [bend_fun(t) for t in timeline_norm]
        bend_value_max = max([abs(value) for value in bend_values_norm]) + 1
        if bend_value_max > 0:
            bend_values_norm = [val/bend_value_max for val in bend_values_norm]
        logger.debug(f"bend_values_norm {bend_values_norm}")
        bend_values = [(val_norm + 1) * PitchBendValues.NORM
                       for val_norm in bend_values_norm]
        logger.debug(f"bend_values {bend_values}")
        chain = [PitchBend(time=time, value=bend)
                 for time, bend in zip(timeline, bend_values)]
        chain = [pitch_bend if start_tick < pitch_bend.time < stop_tick
                 else PitchBend(time=pitch_bend.time, value=PitchBendValues.NORM)
                 for pitch_bend in chain]
        logger.debug(f"chain {chain}")
        return cls(__root__=chain)

    @staticmethod
    def fun_slide_up(x: float) -> float:
        if x == 0:
            return 0
        else:
            return -(1/x)

    @staticmethod
    def fun_parabola_neq(x: float) -> float:
        return -4*x*(x-1)


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


class AllSoundOff(ControlClass):
    name = "All Sound Off"
    code: MidiValue = MidiValue(120)


class AllControllersOff(ControlClass):
    name = "All Controllers Off"
    code: MidiValue = MidiValue(121)


class AllNotesOff(ControlClass):
    name = "All Notes Off"
    code: MidiValue = MidiValue(123)
