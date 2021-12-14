from src.app.model.event import Beat
from src.app.utils.constants import TICKS_PER_BEAT


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
    tick = round(second2tick(second=s, ticks_per_beat=TICKS_PER_BEAT,
                             tempo=bpm2tempo(bpm=bpm)))
    # print("unit2tick", unit, s, tick)
    return tick


def pos2tick(pos: Beat, bpm: float):
    qn_length = 60.0 / bpm
    s = 4 * qn_length * pos
    tick = round(second2tick(second=s, ticks_per_beat=TICKS_PER_BEAT,
                             tempo=bpm2tempo(bpm=bpm)))
    # print("pos2tick", pos, s, tick)
    return tick


def bpm2time_scale(bpm: float):
    time_scale = round(second2tick(second=1, ticks_per_beat=TICKS_PER_BEAT,
                                   tempo=bpm2tempo(bpm=bpm)))
    # print("bpm2time_scale", time_scale)
    return time_scale
