import pytest

from src.app.model.bar import Bar
from src.app.model.event import Event, EventType, Preset, Control, Volume


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
