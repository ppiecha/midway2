from src.app.model.event import Event, EventType
from src.app.model.types import NoteUnit
from src.app.utils.properties import MidiAttr


def test_note(note0):
    print(str(note0.dict(exclude={"parent_id": True})))
    assert note0.dict() == {
        "type": "3-note",
        "channel": 0,
        "beat": 0.0,
        "pitch": 79,
        "unit": NoteUnit.EIGHTH.value,
        "velocity": MidiAttr.DEFAULT_VELOCITY,
        "preset": None,
        "controls": None,
        "pitch_bend_chain": None,
        "active": True,
        "bar_num": None,
    }


def test_bar_constructor(bar1):
    assert len(bar1) == 0


def test_add_note(bar0, note0):
    b0 = bar0 + note0
    assert len(b0) == 1
    assert b0[0] == note0
    assert b0.length() == 1
    for note in b0:
        print(note)
        assert isinstance(note, Event)
        assert note.type == EventType.NOTE


def test_add_two_notes(bar0, note0, note1, bar_result):
    b0 = bar0 + note0 + note1
    print(bar_result)
    assert b0.dict() == bar_result.dict()


def test_add_bars(bar0, bar1, note0, note1, bar_result):
    b0 = bar0 + note0
    b1 = bar1 + note1
    b0 += b1
    assert b0 == bar_result


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
    assert not list(b0.events())


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
        "velocity": MidiAttr.DEFAULT_VELOCITY,
        "preset": {"sf_name": "test", "bank": 0, "patch": 0},
        "controls": None,
        "pitch_bend_chain": None,
        "active": True,
        "bar_num": None,
    }


def test_controls(control0):
    print(control0.dict())
    assert control0.dict() == {
        "type": "1-controls",
        "channel": 0,
        "beat": 0.0,
        "pitch": None,
        "unit": None,
        "velocity": MidiAttr.DEFAULT_VELOCITY,
        "preset": None,
        "controls": [{"class_": {"name": "Volume", "code": 7}, "value": 100}],
        "pitch_bend_chain": None,
        "active": True,
        "bar_num": None,
    }


def test_remove_events_by_type_notes(bar0, note0, note1, note2, note3, two_notes, program0, control0):
    b0 = bar0 + [note0, note1, note2, note3, program0, control0]
    assert len(b0) == 6
    b0.remove_events([note2, note3])
    assert len(b0) == 4
    b0.remove_events_by_type(EventType.CONTROLS)
    assert len(b0) == 3
    b0.remove_events_by_type(EventType.PROGRAM)
    assert list(b0.events()) == two_notes
    b0.remove_events_by_type(EventType.NOTE)
    assert len(b0) == 0


def test_has_event_meta(bar0, program0):
    bar0.add_event(program0)
    assert bar0.has_event(program0)


def test_has_event_note_negative0(bar0, note3, note5):
    bar0.add_event(note3)
    assert bar0.has_event(note5)


def test_has_event_note_negative1(bar1, note4, note6):
    bar1.add_event(note4)
    assert bar1.has_event(note6)


def test_has_event_note_positive(bar0, note3, note2):
    bar0.add_events([note2, note3])


def test_have_same_beat(bar0, note2, note3, note4):
    bar0 += note2
    result = bar0.has_conflict(note3)
    assert result is False
    bar0 += note4
    result = bar0.has_conflict(note2)
    assert result is True
