from src.app.gui.editor.keyboard import PianoKeyboard
from src.app.model.types import MidiValue


def test_piano_keyboard_class():
    keyboard = PianoKeyboard(synth=None, callback=None, channel=0, track_version=None)
    assert keyboard.white_key_position(MidiValue(117)) == 14
