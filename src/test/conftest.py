import pytest

from src.app.backend.composer import Composer
from src.app.mingus.containers.note import Note
from src.app.mingus.core.scales import Major
from src.app.model.bar import Bar
from src.app.model.event import Event, EventType, Preset, Control, Volume
from src.app.model.sequence import Sequence
from src.app.model.track import Track, TrackVersion


@pytest.fixture
def bar0() -> Bar:
    return Bar(bar_num=0)


@pytest.fixture
def bar1() -> Bar:
    return Bar(bar_num=1)


@pytest.fixture
def note0() -> Event:
    return Event(type=EventType.note,
                 channel=0,
                 beat=0,
                 pitch=79,
                 unit=8)


@pytest.fixture
def note1() -> Event:
    return Event(type=EventType.note,
                 channel=0,
                 beat=0.125,
                 pitch=80,
                 unit=8)


@pytest.fixture
def note2() -> Event:
    return Event(type=EventType.note,
                 channel=0,
                 beat=0.250,
                 pitch=81,
                 unit=4)


@pytest.fixture
def note3() -> Event:
    return Event(type=EventType.note,
                 channel=0,
                 beat=0.5,
                 pitch=81,
                 unit=2)


@pytest.fixture
def program0() -> Event:
    return Event(type=EventType.program,
                 channel=0,
                 beat=0,
                 # preset=Preset(sf_name='test', bank=0, patch=0),
                 preset={'sf_name': 'test', 'bank': 0, 'patch': 0})


@pytest.fixture
def control0() -> Event:
    return Event(type=EventType.controls,
                 channel=0,
                 beat=0,
                 controls=[Control(name_code=Volume(), value=100)])


@pytest.fixture()
def sequence(bar0, bar1, note0, note1, program0, control0) -> Sequence:
    sequence = Sequence.from_bars([bar0, bar1])
    sequence.add_events(bar_num=0, events=[note0, program0])
    sequence.add_events(bar_num=1, events=[note1, control0])
    return sequence


@pytest.fixture()
def track_c_major(bar0, bar1) -> Track:
    sequence = Sequence.from_bars([bar0, bar1])
    cmp = Composer(note=Note(name='C'))
    bar0_events = cmp.scale(cls=Major)
    bar1_events = cmp.scale(cls=Major, descending=True)
    sequence.add_events(bar_num=0, events=bar0_events)
    sequence.add_events(bar_num=1, events=bar1_events)
    return Track(name='c major',
                 versions=[TrackVersion.from_sequence(sequence=sequence,
                                                      version_name='c')])

