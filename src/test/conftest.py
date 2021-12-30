import pytest

from src.app.backend.composer import Composer
from src.app.mingus.containers.note import Note
from src.app.mingus.core.scales import Major
from src.app.model.bar import Bar
from src.app.model.event import Event, EventType, Preset
from src.app.model.control import Volume, Control, Expression
from src.app.model.sequence import Sequence
from src.app.model.track import Track, TrackVersion
from src.app.model.types import Bpm, NoteUnit
from src.app.utils.properties import MidiAttr, GuiAttr


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
    return Event(type=EventType.note, channel=0, beat=0, pitch=79, unit=8)


@pytest.fixture
def note1() -> Event:
    return Event(type=EventType.note, channel=0, beat=0.125, pitch=80,
                 unit=NoteUnit.EIGHTH)


@pytest.fixture
def note2() -> Event:
    return Event(type=EventType.note, channel=0, beat=0.250, pitch=81,
                 unit=NoteUnit.QUARTER)


@pytest.fixture
def note3() -> Event:
    return Event(type=EventType.note, channel=0, beat=0.5, pitch=81, unit=NoteUnit.HALF)


@pytest.fixture
def note4() -> Event:
    return Event(type=EventType.note, channel=0, beat=0, pitch=50,
                 unit=NoteUnit.WHOLE, velocity=127)


@pytest.fixture
def program0() -> Event:
    return Event(
        type=EventType.program,
        channel=0,
        beat=0,
        # preset=Preset(sf_name='test', bank=0, patch=0),
        preset={"sf_name": "test", "bank": 0, "patch": 0},
    )


@pytest.fixture
def program_guitar() -> Event:
    return Event(
        type=EventType.program,
        channel=0,
        beat=0,
        preset=Preset(sf_name=MidiAttr.DEFAULT_SF2, bank=0, patch=26),
    )


@pytest.fixture
def program_bass() -> Event:
    return Event(
        type=EventType.program,
        channel=0,
        beat=0,
        preset=Preset(sf_name=MidiAttr.DEFAULT_SF2, bank=0, patch=33),
    )


@pytest.fixture
def program_organ() -> Event:
    return Event(
        type=EventType.program,
        channel=0,
        beat=0,
        preset=Preset(sf_name=MidiAttr.DEFAULT_SF2, bank=0, patch=5),
    )


@pytest.fixture
def control0() -> Event:
    return Event(
        type=EventType.controls,
        channel=0,
        beat=0,
        controls=[Control(class_=Volume(), value=100)],
    )


@pytest.fixture
def control1() -> Event:
    return Event(
        type=EventType.controls,
        channel=0,
        beat=0.25,
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
def track_bass(bar0, bar1, bar2, bar3) -> Track:
    sequence = Sequence.from_bars([bar0, bar1, bar2, bar3])

    return Track(
        name="Bass",
        versions=[TrackVersion.from_sequence(sequence=sequence,
                                             version_name=GuiAttr.DEFAULT_VERSION_NAME)],
    )
