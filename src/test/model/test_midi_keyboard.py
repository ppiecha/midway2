from src.app.model.event import Event, EventType
from src.app.model.midi_keyboard import MidiKeyboard
from src.app.model.types import Midi


def test_midi_keyboard_constructor():
    pad = MidiKeyboard(channel=0)
    key = pad.get_key_by_event(Event(type=EventType.NOTE, pitch=Midi.MAX_B9))
    assert [key.key_top, key.key_bottom] == [0, 14]
    key = pad.get_key_by_event(Event(type=EventType.NOTE, pitch=Midi.MAX_B9 - 1))
    assert [key.key_top, key.key_bottom] == [10, 18]
    key = pad.get_key_by_event(Event(type=EventType.NOTE, pitch=Midi.MAX_B9 - 2))
    assert [key.key_top, key.key_bottom] == [14, 28]
    key = pad.get_key_by_event(Event(type=EventType.NOTE, pitch=Midi.MIN_C1))
    assert [key.key_top, key.key_bottom] == [868, 882]
    print(pad.get_key_by_pos(121))
