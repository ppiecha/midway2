from time import sleep

from src.app.backend.midway_synth import MidwaySynth
from src.app.model.rhythm import Pattern, PatternElementType
from src.app.model.sequence import Sequence
from src.app.model.types import NoteUnit
from src.app.utils.properties import MidiAttr


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


def test_rhythm_pattern(capsys):
    pattern = Pattern.from_str(pattern="4p::1,8a::2,2p::|2p::,2::")
    print(pattern.dict())
    assert len(pattern.versions) == 2
    assert len(pattern.versions[0].elements) == 3
    assert pattern.versions[0].elements[1].value == 8
    assert pattern.versions[0].elements[1].type == PatternElementType.accent
    assert pattern.versions[0].elements[1].repeat == 2


def test_melody_pattern(capsys):
    pattern = Pattern.from_str("4p::1,8a:48-127;50;52-100:2,2p::")
    print(pattern.dict())
    assert len(pattern.versions) == 1
    assert len(pattern.versions[0].elements) == 3
    assert pattern.versions[0].elements[1].value == 8
    assert pattern.versions[0].elements[1].type == PatternElementType.accent
    assert len(pattern.versions[0].elements[1].chord) == 3
    assert pattern.versions[0].elements[1].repeat == 2
    assert pattern.versions[0].elements[1].chord[0].pitch == 48
    assert pattern.versions[0].elements[1].chord[0].velocity == 127
    assert pattern.versions[0].elements[1].chord[1].velocity is None
    assert pattern.versions[0].elements[1].chord[2].velocity == 100


def test_play_rhythm_pattern(capsys):
    bass_drum_bar = Pattern.from_str("2:35:,4:35:2").bar()
    Sequence.set_events_attr(events=bass_drum_bar.events(), attr_val_map={"channel": MidiAttr.DRUM_CHANNEL})
    print(bass_drum_bar)
    MidwaySynth.play_bar(
        bar=bass_drum_bar,
        bpm=120,
        channel=MidiAttr.DRUM_CHANNEL,
        bank=MidiAttr.DRUM_BANK,
        repeat=4,
    )
