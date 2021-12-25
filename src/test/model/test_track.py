from src.app.model.track import TrackVersion, Track


def test_version_constructor(capsys, sequence):
    version = TrackVersion.from_sequence(sequence=sequence)
    print(version.dict())
    assert version.num_of_bars == 2


def test_track(capsys, sequence):
    VER = "test version"
    version = TrackVersion.from_sequence(sequence=sequence, version_name=VER)
    track = Track(name="test track", versions=[version])
    assert len(track.versions) == 1
    assert track.get_version(version_name=VER).num_of_bars == 2
    assert track.get_default_version().sequence.num_of_bars == 2
