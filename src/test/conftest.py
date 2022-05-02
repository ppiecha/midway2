import pytest
from pydantic import PositiveInt

from src.app.backend.composer import Composer
from src.app.backend.midway_synth import MidwaySynth
from src.app.mingus.containers.note import Note
from src.app.mingus.core.scales import Major
from src.app.model.bar import Bar
from src.app.model.composition import Composition
from src.app.model.control import Volume, Control, Expression
from src.app.model.event import Event, EventType, Preset
from src.app.model.rhythm import Rhythm
from src.app.model.sequence import Sequence
from src.app.model.track import Track, TrackVersion, RhythmTrackVersion
from src.app.model.types import Bpm, NoteUnit
from src.app.utils.properties import MidiAttr, DrumPatch


@pytest.fixture
def bpm() -> Bpm:
    return 60


@pytest.fixture
def bar0() -> Bar:
    return Bar(bar_num=0)


@pytest.fixture
def bar1() -> Bar:
    return Bar(bar_num=1)


@pytest.fixture
def bar2() -> Bar:
    return Bar(bar_num=2)


@pytest.fixture
def bar3() -> Bar:
    return Bar(bar_num=3)


@pytest.fixture
def note0() -> Event:
    return Event(type=EventType.NOTE, channel=0, beat=0, pitch=79, unit=NoteUnit.EIGHTH.value)


@pytest.fixture
def note1() -> Event:
    return Event(type=EventType.NOTE, channel=0, beat=NoteUnit.EIGHTH.value, pitch=80, unit=NoteUnit.EIGHTH.value)


@pytest.fixture
def note2() -> Event:
    return Event(type=EventType.NOTE, channel=0, beat=NoteUnit.QUARTER.value, pitch=81, unit=NoteUnit.QUARTER.value)


@pytest.fixture
def note3() -> Event:
    return Event(type=EventType.NOTE, channel=0, beat=NoteUnit.HALF.value, pitch=81, unit=NoteUnit.HALF.value)


@pytest.fixture
def note4() -> Event:
    return Event(
        type=EventType.NOTE,
        channel=0,
        beat=0,
        pitch=50,
        unit=NoteUnit.WHOLE,
        velocity=127,
    )


@pytest.fixture
def note5() -> Event:
    return Event(type=EventType.NOTE, channel=0, beat=NoteUnit.HALF.value, pitch=81, unit=NoteUnit.HALF.value)


@pytest.fixture
def note6() -> Event:
    return Event(
        type=EventType.NOTE,
        channel=0,
        beat=0,
        pitch=50,
        unit=NoteUnit.WHOLE.value,
        velocity=127,
    )


@pytest.fixture
def program0() -> Event:
    return Event(
        type=EventType.PROGRAM,
        channel=0,
        beat=0,
        preset={"sf_name": "test", "bank": 0, "patch": 0},
    )


@pytest.fixture
def program_guitar() -> Event:
    return Event(
        type=EventType.PROGRAM,
        channel=0,
        beat=0,
        preset=Preset(sf_name=MidiAttr.DEFAULT_SF2, bank=0, patch=26),
    )


@pytest.fixture
def program_bass() -> Event:
    return Event(
        type=EventType.PROGRAM,
        channel=0,
        beat=0,
        preset=Preset(sf_name=MidiAttr.DEFAULT_SF2, bank=0, patch=33),
    )


@pytest.fixture
def program_organ() -> Event:
    return Event(
        type=EventType.PROGRAM,
        channel=0,
        beat=0,
        preset=Preset(sf_name=MidiAttr.DEFAULT_SF2, bank=0, patch=5),
    )


@pytest.fixture
def control0() -> Event:
    return Event(
        type=EventType.CONTROLS,
        channel=0,
        beat=0,
        controls=[Control(class_=Volume(), value=100)],
    )


@pytest.fixture
def control1() -> Event:
    return Event(
        type=EventType.CONTROLS,
        channel=0,
        beat=NoteUnit.QUARTER.value,
        controls=[Control(class_=Expression(), value=100)],
    )


@pytest.fixture()
def sequence(bar0, bar1, note0, note1, program0, control0) -> Sequence:
    sequence = Sequence.from_bars([bar0, bar1])
    sequence.add_events(bar_num=0, events=[note0, program0])
    sequence.add_events(bar_num=1, events=[note1, control0])
    return sequence


@pytest.fixture()
def bar_c_major(bar0) -> Bar:
    cmp = Composer(note=Note(name="C"))
    bar0_events = cmp.scale(cls=Major)
    bar0.add_events(events=bar0_events)
    return bar0


@pytest.fixture()
def track_c_major(bar0, bar1) -> Track:
    sequence = Sequence.from_bars([bar0, bar1])
    cmp = Composer(note=Note(name="C"))
    bar0_events = cmp.scale(cls=Major, octaves=2)[:8]
    bar1_events = cmp.scale(cls=Major, octaves=2, descending=True)[:8]
    sequence.add_events(bar_num=0, events=bar0_events)
    sequence.add_events(bar_num=1, events=bar1_events)
    return Track(
        name="c major",
        versions=[TrackVersion.from_sequence(sequence=sequence, version_name="c")],
    )


@pytest.fixture()
def num_of_bars() -> PositiveInt:
    return 4


@pytest.fixture()
def rhythm() -> Rhythm:
    return Rhythm()


@pytest.fixture()
def drums_sequence(rhythm, num_of_bars) -> Sequence:
    bars = [rhythm.bar_of_notes(note_unit=NoteUnit.QUARTER, bar_num=bar_num) for bar_num in range(num_of_bars)]
    sequence = Sequence.from_bars(bars=bars)
    down = [event for index, event in enumerate(sequence.events()) if index % 2 == 0]
    up = [event for index, event in enumerate(sequence.events()) if index % 2 == 1]
    Sequence.set_events_attr(
        events=down,
        attr_val_map={
            "pitch": DrumPatch.ACOUSTIC_BASS_DRUM,
            "velocity": 100,
            "channel": MidiAttr.DRUM_CHANNEL,
        },
    )
    Sequence.set_events_attr(
        events=up,
        attr_val_map={
            "pitch": DrumPatch.ACOUSTIC_SNARE,
            "velocity": 127,
            "channel": MidiAttr.DRUM_CHANNEL,
        },
    )
    return sequence


@pytest.fixture()
def bass_sequence(rhythm, num_of_bars) -> Sequence:
    bars = [rhythm.bar_of_notes(note_unit=NoteUnit.EIGHTH, bar_num=bar_num) for bar_num in range(num_of_bars)]
    return Sequence.from_bars(bars=bars)


@pytest.fixture()
def drums_composition(drums_sequence, bass_sequence, capsys) -> Composition:
    track_version = RhythmTrackVersion(sf_name=MidiAttr.DEFAULT_SF2, sequence=drums_sequence)
    track = Track(name="Drums", versions=[track_version])
    return Composition.from_tracks(tracks=[track], name="drums_composition")


@pytest.fixture(scope="session")
def synth() -> MidwaySynth():
    return MidwaySynth()
