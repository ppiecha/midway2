from src.app.model.composition import Composition


def test_scale_composition(track_c_major):
    composition = Composition.from_tracks(name='test_scale',
                                          tracks=[track_c_major])
    assert len(
        list(composition.default_loop.get_compiled_sequence().events())) == 16


def test_play_custom_composition():
    pass


def test_play_composition():
    pass