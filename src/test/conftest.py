import pytest

from src.app.model.bar import Bar
from src.app.model.note import Event, EventType


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
