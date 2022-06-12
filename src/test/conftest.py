from typing import List

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
from src.app.model.project_version import ProjectVersion
from src.app.model.rhythm import Rhythm
from src.app.model.sequence import Sequence
from src.app.model.track import Track, TrackVersion, RhythmTrackVersion
from src.app.model.types import Bpm, NoteUnit
from src.app.model.variant import Variant, VariantType
from src.app.utils.properties import MidiAttr, DrumPatch


@pytest.fixture
def bpm() -> Bpm:
    return 120


@pytest.fixture(name="bar0")
def fixture_bar0() -> Bar:
    return Bar(bar_num=0)


@pytest.fixture(name="bar1")
def fixture_bar1() -> Bar:
    return Bar(bar_num=1)


@pytest.fixture
def bar2() -> Bar:
    return Bar(bar_num=2)


@pytest.fixture
def bar3() -> Bar:
    return Bar(bar_num=3)


@pytest.fixture(name="note0")
def fixture_note0() -> Event:
    return Event(type=EventType.NOTE, channel=0, beat=0, pitch=79, unit=NoteUnit.EIGHTH.value)


@pytest.fixture(name="note1")
def fixture_note1() -> Event:
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


@pytest.fixture(name="program0")
def fixture_program0() -> Event:
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


@pytest.fixture(name="control0")
def fixture_control0() -> Event:
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


@pytest.fixture(name="sequence")
def fixture_sequence(bar0, bar1, note0, note1, program0, control0) -> Sequence:
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


@pytest.fixture(name="track_c_major")
def fixture_track_c_major(bar0, bar1) -> Track:
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
def bar_c_major_up(track_c_major) -> Bar:
    return track_c_major.get_default_version().get_sequence(include_defaults=True).bars[0]


@pytest.fixture()
def bar_c_major_down(track_c_major) -> Bar:
    return track_c_major.get_default_version().get_sequence(include_defaults=True).bars[1]


@pytest.fixture(name="empty_single_variant")
def fixture_empty_single_variant() -> Variant:
    return Variant(name="empty_single_variant", type=VariantType.SINGLE, selected=True, items=[])


@pytest.fixture(name="empty_composition_variant")
def fixture_empty_composition_variant() -> Variant:
    return Variant(name="empty_composition_variant", type=VariantType.COMPOSITION, selected=True, items=[])


@pytest.fixture(name="variant_c_major_composition")
def fixture_variant_c_major_composition(track_c_major) -> Variant:
    variant = Variant(name="variant_c_major", type=VariantType.COMPOSITION, selected=True, items=[])
    return variant.add_track(track=track_c_major, enable=True)


@pytest.fixture(name="variant_c_major_single")
def fixture_variant_c_major_single(track_c_major) -> Variant:
    variant = Variant(name="variant_c_major", type=VariantType.SINGLE, selected=True, items=[])
    return variant.add_track(track=track_c_major, enable=True)


@pytest.fixture(name="num_of_bars")
def fixture_num_of_bars() -> PositiveInt:
    return 4


@pytest.fixture(name="rhythm")
def fixture_rhythm() -> Rhythm:
    return Rhythm()


@pytest.fixture(name="drums_sequence")
def fixture_drums_sequence(rhythm, num_of_bars) -> Sequence:
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


@pytest.fixture(name="bass_sequence")
def fixture_bass_sequence(rhythm, num_of_bars) -> Sequence:
    bars = [rhythm.bar_of_notes(note_unit=NoteUnit.EIGHTH, bar_num=bar_num) for bar_num in range(num_of_bars)]
    return Sequence.from_bars(bars=bars)


@pytest.fixture()
def drums_composition(drums_sequence) -> Composition | None:
    track_version = RhythmTrackVersion(sf_name=MidiAttr.DEFAULT_SF2, sequence=drums_sequence)
    # track = Track(name="Drums", versions=[track_version])
    # return Composition.from_tracks(tracks=[track], name="drums_composition")


@pytest.fixture(scope="session")
def synth() -> MidwaySynth():
    return MidwaySynth()


@pytest.fixture(name="two_notes")
def fixture_two_notes() -> List:
    return [
        Event(
            **{
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
            }
        ),
        Event(
            **{
                "type": "3-note",
                "channel": 0,
                "beat": NoteUnit.EIGHTH.value,
                "pitch": 80,
                "unit": NoteUnit.EIGHTH.value,
                "velocity": MidiAttr.DEFAULT_VELOCITY,
                "preset": None,
                "controls": None,
                "pitch_bend_chain": None,
                "active": True,
            }
        ),
    ]


@pytest.fixture(name="bar_result")
def fixture_bar_result(two_notes) -> Bar:
    return Bar(
        **{
            "meter": {"denominator": 4, "numerator": 4, "min_unit": 32},
            "bar_num": 0,
            "bar": two_notes,
        }
    )


@pytest.fixture()
def seq_empty_bars() -> Sequence:
    return {
        "bars": {
            0: {
                "meter": {"numerator": 4, "denominator": 4, "min_unit": 32},
                "bar_num": 0,
                "bar": [],
            },
            1: {
                "meter": {"numerator": 4, "denominator": 4, "min_unit": 32},
                "bar_num": 1,
                "bar": [],
            },
        },
    }


@pytest.fixture()
def project_template_file_name() -> str:
    return "C:\\Users\\piotr\\_piotr_\\__GIT__\\Python\\midway2\\src\\app\\default_project.json"


@pytest.fixture(name="empty_project_version")
def fixture_empty_project_version():
    return ProjectVersion(name="empty_project_version")
