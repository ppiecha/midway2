from typing import Dict, List

import pytest

from src.app.backend.midway_synth import MidwaySynth
from src.app.model.bar import Bar
from src.app.model.control import PitchBendChain
from src.app.model.event import Event, EventType, Preset
from src.app.model.types import NoteUnit
from src.app.utils.properties import MidiAttr


@pytest.fixture
def two_notes() -> List:
    return [
        {
            "type": "3-note",
            "channel": 0,
            "beat": 0.0,
            "pitch": 79,
            "unit": 8.0,
            "velocity": None,
            "preset": None,
            "controls": None,
            "pitch_bend_chain": None,
            "active": True,
        },
        {
            "type": "3-note",
            "channel": 0,
            "beat": 0.125,
            "pitch": 80,
            "unit": 8.0,
            "velocity": None,
            "preset": None,
            "controls": None,
            "pitch_bend_chain": None,
            "active": True,
        },
    ]


@pytest.fixture
def bar_result(two_notes) -> Dict:
    return {
        "meter": {"denominator": 4, "numerator": 4},
        "bar_num": 0,
        "bar": two_notes,
    }


def test_note(note0, capsys):
    print(str(note0.dict()))
    assert note0.dict() == {
        "type": "3-note",
        "channel": 0,
        "beat": 0.0,
        "pitch": 79,
        "unit": 8.0,
        "velocity": None,
        "preset": None,
        "controls": None,
        "pitch_bend_chain": None,
        "active": True,
    }


def test_constructor(bar1):
    assert len(bar1) == 0


def test_add_note(bar0, note0, capsys):
    b0 = bar0 + note0
    assert len(b0) == 1
    assert b0[0] == note0
    assert b0.length() == 1
    for note in b0:
        print(note)
        assert isinstance(note, Event)
        assert note.type == EventType.note


def test_add_two_notes(bar0, note0, note1, bar_result):
    b0 = bar0 + note0 + note1
    assert b0.dict() == bar_result


def test_add_bars(bar0, bar1, note0, note1, bar_result):
    b0 = bar0 + note0
    b1 = bar1 + note1
    b0 += b1
    assert b0.dict() == bar_result


def test_bar_notes(bar0, note0, note1, two_notes):
    b0 = bar0 + note0
    b0 += note1
    assert list(b0.events()) == two_notes


def test_event_index(bar0, note0, note1):
    b0 = bar0 + note0
    b0 += note1
    assert b0.event_index(note1) == 1


def test_remove_event(bar0, note0, note1):
    b0 = bar0 + note0
    b0 += note1
    b0.remove_event(event=note0)
    assert list(b0.events()) == [note1]
    b0.remove_event(event=note1)
    assert list(b0.events()) == []


def test_add_events(bar0, note0, note1, note2, two_notes):
    b0 = bar0 + note0
    assert list(b0.events()) == [note0]
    b0 += [note1, note2]
    assert len(b0) == 3
    b0.remove_event(note2)
    assert list(b0.events()) == two_notes


def test_remove_events(bar0, note0, note1, note2, note3, two_notes):
    b0 = bar0 + [note0, note1, note2, note3]
    assert len(b0) == 4
    b0.remove_events([note2, note3])
    assert list(b0.events()) == two_notes


def test_program(program0):
    print(program0.dict())
    assert program0.dict() == {
        "type": "0-program",
        "channel": 0,
        "beat": 0.0,
        "pitch": None,
        "unit": None,
        "velocity": None,
        "preset": {"sf_name": "test", "bank": 0, "patch": 0},
        "controls": None,
        "pitch_bend_chain": None,
        "active": True,
    }


def test_controls(control0, capsys):
    print(control0.dict())
    assert control0.dict() == {
        "type": "1-controls",
        "channel": 0,
        "beat": 0.0,
        "pitch": None,
        "unit": None,
        "velocity": None,
        "preset": None,
        "controls": [{"class_": {"name": "Volume", "code": 7}, "value": 100}],
        "pitch_bend_chain": None,
        "active": True,
    }


def test_play_change_control(bar_c_major, control1, capsys):
    bar_c_major.add_event(event=control1)
    print(bar_c_major)
    MidwaySynth.play_bar(bar=bar_c_major, bpm=120)


def test_play_pitch_bend_parabola(bar0, note4, capsys, program_guitar, bpm):
    pbc = PitchBendChain.gen_chain(
        bend_fun=PitchBendChain.fun_parabola_neq,
        bpm=bpm,
        duration=NoteUnit.WHOLE,
        stop_time=None,
    )
    event0 = Event(
        type=EventType.pitch_bend,
        channel=0,
        beat=0,
        pitch_bend_chain=pbc,
    )
    bar0.add_events([event0, note4, program_guitar])
    MidwaySynth.play_bar(bar=bar0, bpm=bpm)


def test_play_pitch_bend(bar_c_major, capsys, program_guitar):
    bpm = 30
    pitch_bend_chain1 = PitchBendChain.gen_chain(
        bend_fun=PitchBendChain.fun_slide_up, bpm=bpm
    )
    pitch_bend_chain2 = PitchBendChain.gen_chain(
        bend_fun=PitchBendChain.fun_parabola_neq,
        bpm=bpm,
        duration=NoteUnit.EIGHTH,
        stop_time=NoteUnit.THIRTY_SECOND,
    )
    event0 = Event(
        type=EventType.pitch_bend,
        channel=0,
        beat=0.125,
        pitch_bend_chain=pitch_bend_chain2,
    )
    event1 = Event(
        type=EventType.pitch_bend,
        channel=0,
        beat=0.25,
        pitch_bend_chain=pitch_bend_chain1,
    )
    event2 = Event(
        type=EventType.pitch_bend,
        channel=0,
        beat=0.5,
        pitch_bend_chain=pitch_bend_chain2,
    )
    print("pitch bend event", event1)
    bar_c_major.add_events(events=[event0, event1, event2, program_guitar])
    MidwaySynth.play_bar(bar=bar_c_major, bpm=bpm)


def test_remove_events_by_type_notes(
    bar0, note0, note1, note2, note3, two_notes, program0, control0
):
    b0 = bar0 + [note0, note1, note2, note3, program0, control0]
    assert len(b0) == 6
    b0.remove_events([note2, note3])
    assert len(b0) == 4
    b0.remove_events_by_type(EventType.controls)
    assert len(b0) == 3
    b0.remove_events_by_type(EventType.program)
    assert list(b0.events()) == two_notes
    b0.remove_events_by_type(EventType.note)
    assert len(b0) == 0


def test_play_bar_changing_programs(bar_c_major, capsys):
    bar = Bar(bar_num=0)
    for index, event in enumerate(bar_c_major):
        prog_event = Event(
            type=EventType.program,
            channel=0,
            beat=event.beat,
            preset=Preset(sf_name=MidiAttr.DEFAULT_SF2, bank=0, patch=index),
        )
        bar.add_events([prog_event, event])
    MidwaySynth.play_bar(bar=bar, bpm=120)
    bar = Bar(bar_num=0)
    for index, event in enumerate(bar_c_major):
        prog_event = Event(
            type=EventType.program,
            channel=0,
            beat=event.beat,
            preset=Preset(sf_name=MidiAttr.DEFAULT_SF2, bank=0, patch=index + 64),
        )
        bar.add_events([prog_event, event])
    MidwaySynth.play_bar(bar=bar, bpm=120)
