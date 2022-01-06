from src.app.gui.editor.piano_keyboard import PianoKeyboardWidget
from src.app.model.control import MidiValue


def test_piano_keyboard_class(capsys):
    keyboard = PianoKeyboardWidget(synth=None, callback=None, channel=0)
    print(keyboard.white_keys())
    print(keyboard.black_keys())
    assert keyboard.white_key_position(MidiValue(117)) == 14
