from src.app.mingus.core.value import add
from src.app.model.event import EventType, Event, Diff
from src.app.model.meter import invert
from src.app.model.sequence import Sequence
from src.app.model.types import NoteUnit


def test_sequence_constructor():
    seq = Sequence.from_num_of_bars(num_of_bars=1)
    print(seq.dict())
    assert seq.dict() == {
        "bars": {
            0: {
                "meter": {"numerator": 4, "denominator": 4, "min_unit": 32},
                "bar_num": 0,
                "bar": [],
            }
        },
    }


def test_from_bars(bar0, bar1, seq_empty_bars):
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


def test_clear_bar(bar0, bar1, note0, note1, seq_empty_bars):
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


def test_num_of_bars(bar0, bar1, note0, note1, note2, note3, program0, control0):
    sequence = Sequence.from_bars([bar0, bar1])
    sequence.add_events(bar_num=0, events=[note0, note1])
    sequence.add_events(bar_num=1, events=[note2, note3, program0, control0])
    sequence.set_num_of_bars(value=1)
    print(sequence)
    assert sequence.num_of_bars() == 1
    assert list(sequence.events()) == [note0, note1]


def test_remove_event(bar0, note0, note1):
    sequence = Sequence.from_bars([bar0])
    sequence.add_events(bar_num=0, events=[note0, note1])
    assert list(sequence.events()) == [note0, note1]
    sequence.remove_event(bar_num=0, event=note1)
    assert list(sequence.events()) == [note0]


def test_remove_events(bar0, note0, note1):
    sequence = Sequence.from_bars([bar0])
    sequence.add_events(bar_num=0, events=[note0, note1])
    assert list(sequence.events()) == [note0, note1]
    sequence.remove_events(bar_num=0, events=[note0, note1])
    assert not list(sequence.events())


def test_remove_events_by_type(bar0, bar1, note0, note1, program0, control0):
    sequence = Sequence.from_bars([bar0, bar1])
    sequence.add_events(bar_num=0, events=[note0, program0])
    sequence.add_events(bar_num=1, events=[note1, control0])
    sequence.remove_events_by_type(event_type=EventType.CONTROLS)
    assert list(sequence.events()) == [program0, note0, note1]
    sequence.remove_events_by_type(event_type=EventType.PROGRAM)
    assert list(sequence.events()) == [note0, note1]
    sequence.remove_events_by_type(event_type=EventType.NOTE)
    assert not list(sequence.events())


def test_changed_event_beat_pitch(bar0, bar1):
    sequence = Sequence.from_bars([bar0, bar1])
    event = Event(type=EventType.NOTE, pitch=50, beat=NoteUnit.HALF.value, unit=NoteUnit.QUARTER.value, bar_num=0)
    sequence.add_event(bar_num=0, event=event)
    moved_event = sequence.get_changed_event(old_event=event, diff=Diff(beat_diff=NoteUnit.QUARTER.value, pitch_diff=1))
    assert moved_event.bar_num == 0
    assert moved_event.pitch == 51
    assert invert(moved_event.beat) == 0.75
    moved_event = sequence.get_changed_event(
        old_event=moved_event, diff=Diff(beat_diff=NoteUnit.QUARTER.value, pitch_diff=1)
    )
    assert moved_event.bar_num == 1
    assert moved_event.pitch == 52
    assert moved_event.beat == 0.0
    moved_event = sequence.get_changed_event(
        old_event=moved_event, diff=Diff(beat_diff=-NoteUnit.QUARTER.value, pitch_diff=-1)
    )
    assert moved_event.bar_num == 0
    assert moved_event.pitch == 51
    assert invert(moved_event.beat) == 0.75
    moved_event = sequence.get_changed_event(
        old_event=moved_event, diff=Diff(beat_diff=-add(NoteUnit.QUARTER.value, NoteUnit.HALF.value), pitch_diff=-1)
    )
    assert moved_event.bar_num == 0
    assert moved_event.pitch == 50
    assert invert(moved_event.beat) == 0


def test_changed_event_unit(bar0, bar1):
    sequence = Sequence.from_bars([bar0, bar1])
    event = Event(type=EventType.NOTE, pitch=50, beat=NoteUnit.HALF.value, unit=NoteUnit.QUARTER.value, bar_num=0)
    sequence.add_event(bar_num=0, event=event)
    moved_event = sequence.get_changed_event(old_event=event, diff=Diff(unit_diff=NoteUnit.HALF.value))
    assert moved_event.bar_num == 0
    assert moved_event.pitch == 50
    assert moved_event.beat == NoteUnit.HALF.value
    assert moved_event.unit == add(NoteUnit.QUARTER.value, NoteUnit.HALF.value)


def test_copy_bar_from_to(bar0, bar1):
    sequence = Sequence.from_bars([bar0, bar1])
    event0 = Event(type=EventType.NOTE, pitch=50, beat=NoteUnit.HALF.value, unit=NoteUnit.QUARTER.value, bar_num=0)
    sequence.add_event(bar_num=0, event=event0)
    event1 = Event(type=EventType.NOTE, pitch=60, beat=NoteUnit.HALF.value, unit=NoteUnit.QUARTER.value, bar_num=1)
    sequence.add_event(bar_num=1, event=event1)
    sequence.copy_bar_from_to(from_bar_num=0, to_bar_num=1)
    events1 = bar1.events()
    assert len(events1) == 1
    assert events1[0].pitch == 50 and events1[0].bar_num == 1
