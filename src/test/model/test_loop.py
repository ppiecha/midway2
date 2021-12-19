from time import sleep

from src.app.backend.midway_synth import MidwaySynth
from src.app.model.composition import Composition
from src.app.model.event import EventType
from src.app.model.loop import TrackLoopItem, Loop, LoopType, Loops, \
    CompositionLoops
from src.app.model.sequence import Sequence
from src.app.model.track import TrackVersion, Track
from src.app.utils.constants import DEFAULT, FIRST_COMPOSITION_LOOP


def test_scale_loop(track_c_major):
    tli = TrackLoopItem(loop_track=track_c_major,
                        loop_track_version='c',
                        loop_track_enabled=True)
    # print(tli.dict())
    loop = Loop(name='test scale', tracks=[tli])
    assert len(list(loop.get_compiled_sequence().events())) == 16


def test_play_custom_loop(track_c_major, capsys):
    composition = Composition.from_tracks(name='test_scale',
                                          tracks=[track_c_major])
    ms = MidwaySynth()
    ms.play_loop(loops=composition.loops[LoopType.custom], loop_name=DEFAULT,
                 bpm=120, repeat=True)
    while ms.is_playing():
        sleep(0.1)


def test_play_composition_loop(track_c_major, capsys):
    composition = Composition.from_tracks(name='test_scale',
                                          tracks=[track_c_major])
    composition_loops = CompositionLoops.from_list(
        loop_lst=[composition.default_loop,
                  composition.default_loop])
    print(composition_loops)
    assert composition_loops.get_first_loop_name() == '0'
    assert composition_loops.get_next_loop(
        loop_name=FIRST_COMPOSITION_LOOP).name == '1'
    composition.loops[LoopType.composition] = composition_loops
    ms = MidwaySynth()
    ms.play_loop(loops=composition.loops[LoopType.composition],
                 loop_name=FIRST_COMPOSITION_LOOP,
                 bpm=120,
                 repeat=False)
    while ms.is_playing():
        sleep(0.1)
    assert 1 == 0


def test_play_compiled_loop(track_c_major, capsys):
    up_bar = track_c_major.get_default_version() \
        .get_sequence(include_defaults=True).bars[0]
    down_bar = track_c_major.get_default_version() \
        .get_sequence(include_defaults=True).bars[1]
    up_bar0 = up_bar.copy(deep=True)
    up_bar0.bar_num = 0
    up_bar1 = up_bar.copy(deep=True)
    up_bar1.bar_num = 1
    down_bar0 = down_bar.copy(deep=True)
    down_bar0.bar_num = 0
    down_bar1 = down_bar.copy(deep=True)
    down_bar1.bar_num = 1
    s1 = Sequence.from_bars([up_bar0, down_bar1])
    s2 = Sequence.from_bars([down_bar0, up_bar1])
    v1 = TrackVersion.from_sequence(sequence=s1)
    v2 = TrackVersion.from_sequence(sequence=s2)
    t1 = Track(name='t1', versions=[v1])
    t2 = Track(name='t2', versions=[v2])
    c = Composition.from_tracks(tracks=[t1, t2])
    ms = MidwaySynth()
    ms.play_custom_loop(composition=c, bpm=60)
    while ms.is_playing():
        sleep(0.1)
