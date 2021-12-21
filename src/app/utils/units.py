from math import floor, ceil
from typing import NamedTuple

from pydantic import NonNegativeInt

from src.app.model.event import Beat, Unit, Bpm
from src.app.utils.constants import TICKS_PER_BEAT


class BarBeat(NamedTuple):
    bar: NonNegativeInt
    beat: Beat


def tick2second(tick, ticks_per_beat, tempo) -> float:
    """Convert absolute time in ticks to seconds.

    Returns absolute time in seconds for a chosen MIDI file time
    resolution (ticks per beat, also called PPQN or pulses per quarter
    note) and tempo (microseconds per beat).
    """
    scale = tempo * 1e-6 / ticks_per_beat
    return tick * scale


def second2tick(second, ticks_per_beat, tempo) -> int:
    """Convert absolute time in seconds to ticks.

    Returns absolute time in ticks for a chosen MIDI file time
    resolution (ticks per beat, also called PPQN or pulses per quarter
    note) and tempo (microseconds per beat).
    """
    scale = tempo * 1e-6 / ticks_per_beat
    return second / scale


def bpm2tempo(bpm) -> int:
    """Convert beats per minute to MIDI file tempo.

    Returns microseconds per beat as an integer::

        240 => 250000
        120 => 500000
        60 => 1000000
    """
    # One minute is 60 million microseconds.
    return int(round((60 * 1000000) / bpm))


def tempo2bpm(tempo) -> Bpm:
    """Convert MIDI file tempo to BPM.

    Returns BPM as an integer or float::

        250000 => 240
        500000 => 120
        1000000 => 60
    """
    # One minute is 60 million microseconds.
    return (60 * 1000000) / tempo


def unit2tick(unit: Unit, bpm: Bpm) -> int:
    if unit == 0:
        return 0
    qn_length = 60.0 / bpm
    second = qn_length * (4.0 / unit)
    tick = round(second2tick(second=second, ticks_per_beat=TICKS_PER_BEAT,
                             tempo=bpm2tempo(bpm=bpm)))
    return tick


def beat2tick(beat: Beat, bpm: Bpm) -> int:
    qn_length = 60.0 / bpm
    second = 4 * qn_length * beat
    tick = round(second2tick(second=second, ticks_per_beat=TICKS_PER_BEAT,
                             tempo=bpm2tempo(bpm=bpm)))
    return tick


def bpm2time_scale(bpm: float):
    time_scale = round(second2tick(second=1, ticks_per_beat=TICKS_PER_BEAT,
                                   tempo=bpm2tempo(bpm=bpm)))
    return time_scale


def bar_beat2pos(bar_beat: BarBeat, cell_unit: Unit, cell_width: int) -> float:
    return (bar_beat.bar + bar_beat.beat) * cell_unit * cell_width


def pos2bar_beat(pos: float, cell_unit: Unit, cell_width: int) -> BarBeat:
    bar_width = cell_unit + cell_width
    bar = floor(pos / bar_width)
    pos = pos - (bar * bar_width)
    beat_width = ceil(pos / cell_width) * cell_width
    beat = beat_width / bar_width
    return BarBeat(bar=bar, beat=beat)


def round2cell(pos: float, cell_width: int) -> float:
    return floor(pos / cell_width) * cell_width


def