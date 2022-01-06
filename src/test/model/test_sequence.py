import pytest

from src.app.model.event import EventType, Event
from src.app.model.sequence import Sequence, BarNumEvent


@pytest.fixture()
def seq_empty_bars() -> Sequence:
    return {
        "bars": {
            0: {
                "meter": {"numerator": 4, "denominator": 4},
                "bar_num": 0,
                "bar": [],
            },
            1: {
                "meter": {"numerator": 4, "denominator": 4},
                "bar_num": 1,
                "bar": [],
            },
        },
    }


def test_constructor(capsys):
    seq = Sequence.from_num_of_bars(num_of_bars=1)
    print(seq.dict())
    assert seq.dict() == {
        "bars": {
            0: {
                "meter": {"numerator": 4, "denominator": 4},
                "bar_num": 0,
                "bar": [],
            }
        },
    }


def test_from_bars(bar0, bar1, capsys, seq_empty_bars):
    sequence = Sequence.from_bars([bar0, bar1])
    print(sequence.dict())
    assert sequence.dict() == seq_empty_bars


def test_add_event(bar0, bar1, note0):
    sequence = Sequence.from_bars([bar0, bar1])
    sequence.add_event(bar_num=0, event=note0)
    assert list(sequence.events()) == [note0]


def test_add_events(bar0, bar1, note0, note1, note2, note3):
    sequence = Sequence.from_bars([bar0, bar1])
    sequence.add_events(bar_num=0, events=[note0, note1])
    sequence.add_events(bar_num=1, events=[note2, note3])
    assert list(sequence[0].events()) == [note0, note1]
    assert list(sequence[1].events()) == [note2, note3]


def test_clear_bar(bar0, bar1, note0, note1, note2, note3, seq_empty_bars):
    sequence = Sequence.from_bars([bar0, bar1])
    sequence.add_events(bar_num=0, events=[note0, note1])
    sequence.clear_bar(bar_num=0)
    assert sequence.dict() == seq_empty_bars


def test_clear(bar0, bar1, note0, note1, note2, note3, seq_empty_bars):
    sequence = Sequence.from_bars([bar0, bar1])
    sequence.add_events(bar_num=0, events=[note0, note1])
    sequence.add_events(bar_num=1, events=[note2, note3])
    sequence.clear()
    assert sequence.dict() == seq_empty_bars


def test_events(bar0, bar1, note0, note1, note2, note3, program0, control0):
    sequence = Sequence.from_bars([bar0, bar1])
    sequence.add_events(bar_num=0, events=[note0, note1])
    sequence.add_events(bar_num=1, events=[note2, note3, program0, control0])
    l1 = list(sequence.events())
    l2 = [note0, note1, note2, note3, program0, control0]
    l3 = [item for item in l1 if item in l2]
    assert l1 == l3


def test_total_length(bar0, bar1):
    sequence = Sequence.from_bars([bar0, bar1])
    assert sequence.num_of_bars() == 2


def test_num_of_bars(
    bar0, bar1, note0, note1, note2, note3, program0, control0, capsys
):
    sequence = Sequence.from_bars([bar0, bar1])
    sequence.add_events(bar_num=0, events=[note0, note1])
    sequence.add_events(bar_num=1, events=[note2, note3, program0, control0])
    sequence.set_num_of_bars(value=1)
    print(sequence)
    assert sequence.num_of_bars() == 1
    assert list(sequence.events()) == [note0, note1]


def test_remove_event(
    bar0, bar1, note0, note1, note2, note3, program0, control0, capsys
):
    sequence = Sequence.from_bars([bar0])
    sequence.add_events(bar_num=0, events=[note0, note1])
    assert list(sequence.events()) == [note0, note1]
    sequence.remove_event(bar_num=0, event=note1)
    assert list(sequence.events()) == [note0]


def test_remove_events(
    bar0, bar1, note0, note1, note2, note3, program0, control0, capsys
):
    sequence = Sequence.from_bars([bar0])
    sequence.add_events(bar_num=0, events=[note0, note1])
    assert list(sequence.events()) == [note0, note1]
    sequence.remove_events(bar_num=0, events=[note0, note1])
    assert list(sequence.events()) == []


def test_remove_events_by_type(
    bar0, bar1, note0, note1, note2, note3, program0, control0, capsys
):
    sequence = Sequence.from_bars([bar0, bar1])
    sequence.add_events(bar_num=0, events=[note0, program0])
    sequence.add_events(bar_num=1, events=[note1, control0])
    sequence.remove_events_by_type(event_type=EventType.CONTROLS)
    assert list(sequence.events()) == [program0, note0, note1]
    sequence.remove_events_by_type(event_type=EventType.PROGRAM)
    assert list(sequence.events()) == [note0, note1]
    sequence.remove_events_by_type(event_type=EventType.NOTE)
    assert list(sequence.events()) == []


def test_move_event(bar0, bar1, capsys):
    sequence = Sequence.from_bars([bar0, bar1])
    event = Event(type=EventType.NOTE, pitch=50, beat=0.5)
    sequence.add_event(bar_num=0, event=event)
    moved_event = sequence.move_event(
        BarNumEvent(bar_num=0, event=event), beat_diff=0.25, pitch_diff=1
    )
    assert moved_event.bar_num == 0
    assert moved_event.event.pitch == 51
    assert moved_event.event.beat == 0.75
    moved_event = sequence.move_event(
        BarNumEvent(bar_num=0, event=moved_event.event), beat_diff=0.25, pitch_diff=1
    )
    assert moved_event.bar_num == 1
    assert moved_event.event.pitch == 52
    assert moved_event.event.beat == 0.0
