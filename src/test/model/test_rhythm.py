from src.app.model.rhythm import Pattern, PatternElementType
from src.app.model.types import NoteUnit


def test_bar_of_notes(rhythm):
    bar = rhythm.bar_of_notes(note_unit=NoteUnit.QUARTER)
    print(bar)
    assert len(bar) == 4


def test_rhythm_pattern():
    pattern = Pattern.from_str(pattern="4p::1,8a::2,2p::|2p::,2::")
    print(pattern.dict())
    assert len(pattern.versions) == 2
    assert len(pattern.versions[0].elements) == 3
    assert pattern.versions[0].elements[1].value == 8
    assert pattern.versions[0].elements[1].type == PatternElementType.accent
    assert pattern.versions[0].elements[1].repeat == 2


def test_melody_pattern():
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
