import logging
import os
from typing import Dict

import constants
from lib4py.logger import get_console_logger

from src.app.constants import SF2_PATH

logger = get_console_logger(name=__name__, log_level=logging.INFO)

TICKS_PER_BEAT = 96
MAX_MIDI = 128
MAX_CHANNEL = 256

# TODO read all soundfonts from folder
DEFAULT_SF2 = os.path.join(SF2_PATH, "ChoriumRevA.SF2")
SF2_FLUID = os.path.join(SF2_PATH, "FluidR3.sf2")
DEFAULT_BANK = 0
DEFAULT_PATCH = 0
DEFAULT_VELOCITY = 100
DEFAULT_VERSION_NAME = "Default"

CHANNELS = [channel for channel in range(MAX_CHANNEL)]

CONTROL_CODE: Dict[str, int] = {
    'Modulation Wheel': 1,
    'Volume': 7,
    'Pan': 10,
    'Expression': 11,
    'Sustain Pedal': 64,
    'Filter Resonance': 71,
    'Release Time': 72,
    'Attack Time': 74,
    'Cutoff Frequency': 74,
    'Decay Time': 75,
    'Vibrato Rate': 76,
    'Vibrato Depth': 77,
    'Vibrato Delay': 78,
    'Reverb': 91,
    'Chorus': 93,
    'Registered Parameter Number LSB': 100,
    'Registered Parameter Number MSB': 101,
    'All Controllers Off': 121,
    'All Notes Off': 123
}

CONTROL_KEY = {
    "0: Bank Select": 0,
    "1: Modulation Wheel or Lever": 1,
    "2: Breath Controller": 2,
    "4: Foot Controller": 4,
    "5: Portamento Time": 5,
    "7: Channel Volume": 7,
    "8: Balance": 8,
    "10: Pan": 10,
    "11: Expression Controller": 11,
    "12: Effect Control": 12,
    "64: Damper Pedal": 64,
    "65: Portamento": 65,
    "84: Amount of Portamento": 84,
    "91: Reverb": 91,
    "93: Chorus": 93
}

CONTROL_NAME = {
    0: "0: Bank Select",
    1: "1: Modulation Wheel or Lever",
    2: "2: Breath Controller",
    4: "4: Foot Controller",
    5: "5: Portamento Time",
    7: "7: Channel Volume",
    8: "8: Balance",
    10: "10: Pan",
    11: "11: Expression Controller",
    12: "12: Effect Control",
    64: "64: Damper Pedal",
    65: "65: Portamento",
    84: "84: Amount of Portamento",
    91: "91: Reverb",
    93: "93: Chorus"
}


def tick2second(tick, ticks_per_beat, tempo):
    """Convert absolute time in ticks to seconds.

    Returns absolute time in seconds for a chosen MIDI file time
    resolution (ticks per beat, also called PPQN or pulses per quarter
    note) and tempo (microseconds per beat).
    """
    scale = tempo * 1e-6 / ticks_per_beat
    return tick * scale


def second2tick(second, ticks_per_beat, tempo):
    """Convert absolute time in seconds to ticks.

    Returns absolute time in ticks for a chosen MIDI file time
    resolution (ticks per beat, also called PPQN or pulses per quarter
    note) and tempo (microseconds per beat).
    """
    scale = tempo * 1e-6 / ticks_per_beat
    # print("second2tick", second, scale, tempo, second / scale)
    return second / scale


def bpm2tempo(bpm):
    """Convert beats per minute to MIDI file tempo.

    Returns microseconds per beat as an integer::

        240 => 250000
        120 => 500000
        60 => 1000000
    """
    # One minute is 60 million microseconds.
    return int(round((60 * 1000000) / bpm))


def tempo2bpm(tempo):
    """Convert MIDI file tempo to BPM.

    Returns BPM as an integer or float::

        250000 => 240
        500000 => 120
        1000000 => 60
    """
    # One minute is 60 million microseconds.
    return (60 * 1000000) / tempo


def unit2tick(unit: float, bpm: float):
    if unit == 0:
        return 0
    qn_length = 60.0 / bpm
    s = qn_length * (4.0 / unit)
    tick = round(second2tick(second=s, ticks_per_beat=TICKS_PER_BEAT, tempo=bpm2tempo(bpm=bpm)))
    # print("unit2tick", unit, s, tick)
    return tick


def pos2tick(pos: float, bpm: float):
    qn_length = 60.0 / bpm
    s = 4 * qn_length * pos
    tick = round(second2tick(second=s, ticks_per_beat=TICKS_PER_BEAT, tempo=bpm2tempo(bpm=bpm)))
    # print("pos2tick", pos, s, tick)
    return tick


def bpm2time_scale(bpm: float):
    time_scale = round(second2tick(second=1, ticks_per_beat=TICKS_PER_BEAT, tempo=bpm2tempo(bpm=bpm)))
    # print("bpm2time_scale", time_scale)
    return time_scale


class BarProps:
    def __init__(self, bar_num: int, start_tick: int, duration: int):
        self.bar_num: int = bar_num
        self.start_tick = start_tick
        self.duration = duration
