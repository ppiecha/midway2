from src.app.model.composition import Composition


def test_scale_composition(track_c_major):
    composition = Composition(name='test_scale', tracks=[track_c_major])
    composition.update_default_loop()
    assert len(
        list(composition.get_default_loop().get_sequence().events())) == 16
