from time import sleep

from src.app.backend.fs import FS
from src.app.model.composition import Composition
from src.app.model.event import Preset, LoopType
from src.app.utils.constants import DEFAULT_SF2, SF2_FLUID, DEFAULT


def test_scale_composition(track_c_major):
    composition = Composition.from_tracks(name='test_scale',
                                          tracks=[track_c_major])
    assert len(
        list(composition.default_loop.get_compiled_sequence().events())) == 16


def test_play_custom_loop(track_c_major, capsys):
    composition = Composition.from_tracks(name='test_scale',
                                          tracks=[track_c_major])
    print(composition)
    fs = FS()
    preset = Preset(sf_name=SF2_FLUID, bank=0, patch=0)
    fs.preset_change(channel=0, preset=preset)
    # fs.play_composition(composition=composition, loop_type=LoopType.custom,
    #                     loop_name=DEFAULT, bpm=60)
    fs.play_loop(loops=composition.loops[LoopType.custom], loop_name=DEFAULT,
                 bpm=60, repeat=True)
    print('preset', fs.get_current_preset(channel=0))
    while fs.is_playing():
        print('playing')
        sleep(0.5)
    assert 1 == 0


def test_play_composition_loop(track_c_major, capsys):
    pass


def test_get_compiled_sequence(track_c_major, capsys):
    pass
