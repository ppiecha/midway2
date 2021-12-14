from src.app.model.loop import TrackLoopItem, Loop


def test_scale_loop(track_c_major):
    tli = TrackLoopItem(loop_track=track_c_major,
                        loop_track_version='c',
                        loop_track_enabled=True)
    print(tli.dict())
    loop = Loop(name='test scale', tracks=[tli])
    assert len(list(loop.get_compiled_sequence().events())) == 16
