from time import sleep

from src.app.backend.midway_synth import MidwaySynth
from src.app.model.composition import Composition
from src.app.model.loop import TrackLoopItem, Loop, LoopType, Loops, \
    CompositionLoops
from src.app.model.sequence import Sequence
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
    fs = MidwaySynth()
    fs.play_loop(loops=composition.loops[LoopType.custom], loop_name=DEFAULT,
                 bpm=120, repeat=True)
    while fs.is_playing():
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
    fs = MidwaySynth()
    fs.play_loop(loops=composition.loops[LoopType.composition],
                 loop_name=FIRST_COMPOSITION_LOOP,
                 bpm=120,
                 repeat=False)
    while fs.is_playing():
        sleep(0.1)
    assert 1 == 0


def test_get_compiled_sequence(track_c_major, capsys):
    up_bar = track_c_major.get_default_version() \
        .get_sequence(include_defaults=True).bars[0]
    down_bar = track_c_major.get_default_version() \
        .get_sequence(include_defaults=True).bars[1]
    sequence1 = Sequence.from_bars([up_bar, down_bar])
    sequence2 = Sequence.from_bars([down_bar, up_bar])

    pass
