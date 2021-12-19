from time import sleep

from src.app.backend.midway_synth import MidwaySynth
from src.app.model.composition import Composition
from src.app.model.loop import CompositionLoops, LoopType
from src.app.utils.constants import FIRST_COMPOSITION_LOOP


def test_scale_composition(track_c_major):
    composition = Composition.from_tracks(name='test_scale',
                                          tracks=[track_c_major])
    assert len(
        list(composition.default_loop.get_compiled_sequence().events())) == 16


def test_play_custom_composition(track_c_major):
    composition = Composition.from_tracks(name='test_scale',
                                          tracks=[track_c_major])
    ms = MidwaySynth()
    ms.play_custom_loop(composition=composition, bpm=90, repeat=False)
    while ms.is_playing():
        sleep(0.1)


def test_play_composition(track_c_major):
    composition = Composition.from_tracks(name='test_scale',
                                          tracks=[track_c_major])
    composition_loops = CompositionLoops.from_list(
        loop_lst=[composition.default_loop,
                  composition.default_loop])
    assert composition_loops.get_first_loop_name() == '0'
    assert composition_loops.get_next_loop(
        loop_name=FIRST_COMPOSITION_LOOP).name == '1'
    composition.loops[LoopType.composition] = composition_loops
    ms = MidwaySynth()
    ms.play_composition_loop(composition=composition, bpm=90, repeat=False)
    while ms.is_playing():
        sleep(0.1)