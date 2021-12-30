from time import sleep

from src.app.backend.midway_synth import MidwaySynth
from src.app.model.types import NoteUnit


def test_bar_of_notes(rhythm, capsys):
    bar = rhythm.bar_of_notes(note_unit=NoteUnit.QUARTER)
    print(bar)
    assert len(bar) == 4


def test_play_drums_composition(drums_composition):
    ms = MidwaySynth()
    print(drums_composition)
    ms.play_custom_loop(composition=drums_composition, bpm=100, repeat=False)
    while ms.is_playing():
        sleep(0.1)
