import pytest

from src.app.model.sequence import Sequence


@pytest.fixture()
def seq_empty_bars():
    return {'numerator': 4,
            'denominator': 4,
            'num_of_bars': 2,
            'bars': {0: {"numerator": 4,
                         "denominator": 4,
                         "bar_num": 0,
                         "length": 1.0,
                         "bar": []
                         },
                     1: {"numerator": 4,
                         "denominator": 4,
                         "bar_num": 1,
                         "length": 1.0,
                         "bar": []
                         }
                     }
            }


def test_constructor(capsys):
    seq = Sequence(num_of_bars=1)
    print(seq.dict())
    assert seq.dict() == {'numerator': 4, 'denominator': 4, 'num_of_bars': 1,
                          'bars': {0: {'numerator': 4, 'denominator': 4,
                                       'bar_num': 0, 'length': 1.0,
                                       'bar': []}}}


def test_from_bars(bar0, bar1, capsys, seq_empty_bars):
    sequence = Sequence.from_bars([bar0, bar1])
    print(sequence.dict())
    assert sequence.dict() == seq_empty_bars


def test_add_event(bar0, bar1, note0):
    sequence = Sequence.from_bars([bar0, bar1])
    sequence.add_event(bar_num=0, event=note0)
    assert list(sequence.events()) == [note0]


def test_add_events(bar0, bar1, note0, note1, note2, note3):
    sequence = Sequence.from_bars([bar0, bar1])
    sequence.add_events(bar_num=0, events=[note0, note1])
    sequence.add_events(bar_num=1, events=[note2, note3])
    assert list(sequence[0].events()) == [note0, note1]
    assert list(sequence[1].events()) == [note2, note3]


def test_clear_bar(bar0, bar1, note0, note1, note2, note3, seq_empty_bars):
    sequence = Sequence.from_bars([bar0, bar1])
    sequence.add_events(bar_num=0, events=[note0, note1])
    sequence.clear_bar(bar_num=0)
    assert sequence.dict() == seq_empty_bars


def test_clear(bar0, bar1, note0, note1, note2, note3, seq_empty_bars):
    sequence = Sequence.from_bars([bar0, bar1])
    sequence.add_events(bar_num=0, events=[note0, note1])
    sequence.add_events(bar_num=1, events=[note2, note3])
    sequence.clear()
    assert sequence.dict() == seq_empty_bars


def test_events(bar0, bar1, note0, note1, note2, note3, program0, control0):
    sequence = Sequence.from_bars([bar0, bar1])
    sequence.add_events(bar_num=0, events=[note0, note1])
    sequence.add_events(bar_num=1, events=[note2, note3, program0, control0])
    l1 = list(sequence.events())
    l2 = [note0, note1, note2, note3, program0, control0]
    l3 = [item for item in l1 if item in l2]
    assert l1 == l3


def test_num_of_bars(bar0, bar1, note0, note1, note2, note3, program0,
                     control0, capsys):
    sequence = Sequence.from_bars([bar0, bar1])
    sequence.add_events(bar_num=0, events=[note0, note1])
    sequence.add_events(bar_num=1, events=[note2, note3, program0, control0])
    sequence.set_num_of_bars(value=1)
    print(sequence)
    assert sequence.num_of_bars == 1
    assert list(sequence.events()) == [note0, note1]


def test_remove_event():
    pass


def test_remove_events():
    pass


def test_remove_events_by_type():
    pass
