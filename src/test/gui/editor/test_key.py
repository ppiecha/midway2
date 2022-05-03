from src.app.gui.editor.key import MetaKey
from src.app.model.event import EventType
from src.app.model.midi_keyboard import MidiKey


def test_meta_key_str():
    meta_key = MetaKey(
        base_key=MidiKey(event_type=EventType.NOTE, channel=0, key_top=0, key_bottom=0), keyboard=None, callback=None
    )
    assert str(meta_key) == "Not supported key event type"
