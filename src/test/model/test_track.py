from src.app.model.track import TrackVersion, Track


def test_version_constructor(sequence):
    version = TrackVersion.from_sequence(sequence=sequence)
    print(version.dict())
    assert version.num_of_bars() == 2


def test_track(sequence):
    ver = "test version"
    version = TrackVersion.from_sequence(sequence=sequence, version_name=ver)
    track = Track(name="test track", versions=[version])
    assert len(track.versions) == 1
    assert track.get_version(version_name=ver).num_of_bars() == 2
    assert track.get_default_version().sequence.num_of_bars() == 2
