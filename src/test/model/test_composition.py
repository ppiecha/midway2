from time import sleep

from src.app.backend.synth import FS
from src.app.model.composition import Composition
from src.app.model.event import Preset
from src.app.utils.constants import DEFAULT_SF2, SF2_FLUID


def test_scale_composition(track_c_major):
    composition = Composition(name='test_scale', tracks=[track_c_major])
    composition.update_default_loop()
    assert len(
        list(composition.get_default_loop().get_sequence().events())) == 16


def test_play_composition(track_c_major, capsys):
    composition = Composition(name='test_scale', tracks=[track_c_major])
    composition.update_default_loop()
    fs = FS()
    preset = Preset(sf_name=SF2_FLUID, bank=0, patch=0)
    fs.preset_change(channel=0, preset=preset)
    fs.play_composition(composition=composition, bpm=60)
    print('preset', fs.get_current_preset(channel=0))
    # while fs.is_playing():
    #     # print('playing')
    #     sleep(0.5)
    sleep(10)
    assert 1 == 0
