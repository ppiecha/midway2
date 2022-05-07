from time import sleep

from src.app.model.composition import Composition
from src.app.model.loop import CompositionLoops, LoopType
from src.app.utils.properties import GuiAttr


def test_scale_composition(track_c_major):
    composition = Composition.from_tracks(name="test_scale", tracks=[track_c_major])
    assert len(list(composition.default_loop.get_compiled_sequence().events())) == 16


def test_play_custom_composition(track_c_major, synth):
    composition = Composition.from_tracks(name="test_scale", tracks=[track_c_major])
    synth.play_custom_loop(composition=composition, bpm=120, repeat=False)
    while synth.is_playing():
        sleep(0.1)


def test_play_composition(track_c_major, synth):
    composition = Composition.from_tracks(name="test_scale", tracks=[track_c_major])
    composition_loops = CompositionLoops.from_list(loop_lst=[composition.default_loop, composition.default_loop])
    assert composition_loops.get_first_loop_name() == "0"
    assert composition_loops.get_next_loop(loop_name=GuiAttr.FIRST_COMPOSITION_LOOP).name == "1"
    composition.loops[LoopType.composition] = composition_loops
    synth.play_composition_loop(composition=composition, bpm=120, repeat=False)
    while synth.is_playing():
        sleep(0.1)
