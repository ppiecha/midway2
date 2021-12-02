import json
from typing import Dict, List

import pytest

from src.app.model.bar import Bar
from src.app.model.note import EventType, Event


@pytest.fixture
def bar0() -> Bar:
    return Bar(bar_num=0)


@pytest.fixture
def bar1() -> Bar:
    return Bar(bar_num=1)


@pytest.fixture
def note0() -> Event:
    return Event(type=EventType.note,
                 channel=0,
                 beat=0,
                 pitch=79,
                 unit=8)


@pytest.fixture
def note1() -> Event:
    return Event(type=EventType.note,
                 channel=0,
                 beat=0.125,
                 pitch=80,
                 unit=8)


@pytest.fixture
def note2() -> Event:
    return Event(type=EventType.note,
                 channel=0,
                 beat=0.250,
                 pitch=81,
                 unit=4)


@pytest.fixture
def note3() -> Event:
    return Event(type=EventType.note,
                 channel=0,
                 beat=0.5,
                 pitch=81,
                 unit=2)


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


def test_note(note0):
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


def test_remove_events_by_type_notes():
    pass
