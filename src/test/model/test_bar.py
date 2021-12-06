from typing import Dict, List

import pytest

from src.app.model.event import Event, EventType


@pytest.fixture
def two_notes() -> List:
    return [
        {
            "type": "note",
            "channel": 0,
            "beat": 0.0,
            "pitch": 79,
            "unit": 8.0,
            "velocity": None,
            "preset": None,
            "controls": None
        },
        {
            "type": "note",
            "channel": 0,
            "beat": 0.125,
            "pitch": 80,
            "unit": 8.0,
            "velocity": None,
            "preset": None,
            "controls": None
        }]


@pytest.fixture
def bar_result(two_notes) -> Dict:
    return {
        "numerator": 4,
        "denominator": 4,
        "bar_num": 0,
        "length": 1,
        "bar": two_notes}


def test_note(note0, capsys):
    print(str(note0.dict()))
    assert note0.dict() == {"type": "note",
                            "channel": 0,
                            "beat": 0.0,
                            "pitch": 79,
                            "unit": 8.0,
                            "velocity": None,
                            "preset": None,
                            "controls": None
                            }


def test_constructor(bar1):
    assert len(bar1) == 0


def test_add_note(bar0, note0, capsys):
    b0 = bar0 + note0
    assert (len(b0) == 1)
    assert (b0[0] == note0)
    assert (b0.length == 1)
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
    assert program0.dict() == {"type": "program",
                               "channel": 0,
                               "beat": 0.0,
                               "pitch": None,
                               "unit": None,
                               "velocity": None,
                               "preset": {'sf_name': 'test', 'bank': 0,
                                          'patch': 0},
                               "controls": None
                               }


def test_controls(control0, capsys):
    print(control0.dict())
    assert control0.dict() == {"type": "controls",
                               "channel": 0,
                               "beat": 0.0,
                               "pitch": None,
                               "unit": None,
                               "velocity": None,
                               "preset": None,
                               "controls": [{'name_code': {'name': 'Volume',
                                                           'code': 7},
                                             'value': 100}]
                               }


def test_pitch_bend():
    pass


def test_remove_events_by_type_notes(bar0, note0, note1, note2, note3,
                                     two_notes, program0, control0):
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
