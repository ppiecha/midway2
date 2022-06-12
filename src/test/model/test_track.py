from uuid import uuid4

import pytest

from src.app.model.track import TrackVersion, Track

from src.app.model.types import TrackType
from src.app.utils.exceptions import NoDataFound, DuplicatedName


def test_version_constructor(sequence):
    version = TrackVersion.from_sequence(sequence=sequence)
    assert version.num_of_bars() == 2


def test_version_to_string(sequence):
    version = TrackVersion.from_sequence(sequence=sequence)
    assert version.json()


def test_track(sequence):
    ver = "test version"
    version = TrackVersion.from_sequence(sequence=sequence, version_name=ver)
    track = Track(name="test track", versions=[version])
    assert len(track.versions) == 1
    assert track.get_version(identifier=ver).num_of_bars() == 2
    assert track.get_default_version().sequence.num_of_bars() == 2


class TestTrackVersion:
    def test_from_sequence(self, sequence):
        version = TrackVersion.from_sequence(sequence=sequence)
        assert version.num_of_bars() == 2

    def test_get_sequence(self, sequence):
        version = TrackVersion.from_sequence(sequence=sequence)
        assert sequence == version.get_sequence()


class TestTrack:
    def test_from_sequence(self, sequence):
        track = Track.from_sequence(sequence=sequence)
        assert track.type == TrackType.VOICE and len(track.versions) == 1

    def test_get_version(self, sequence):
        version_name = "index 0 item"
        track = Track.from_sequence(name="TestTrack::test_get_version", version_name=version_name, sequence=sequence)
        assert len(track.versions) == 1
        assert track.versions[0] == track.get_version(identifier=version_name)
        assert track.versions[0] == track.get_version(identifier=track.versions[0].id)

    def test_get_version_neg(self, sequence):
        version_name = "index 0 item"
        track = Track.from_sequence(name="TestTrack::test_get_version", version_name=version_name, sequence=sequence)
        assert len(track.versions) == 1
        with pytest.raises(NoDataFound):
            track.get_version(identifier="wrong name")
        track = Track(name="Empty")
        assert track.get_version(identifier="wrong name", raise_not_found=False) is None
        with pytest.raises(NoDataFound):
            track.get_version(identifier="wrong name")
        assert track.get_version(identifier=uuid4(), raise_not_found=False) is None

    def test_add_track_version(self, sequence):
        version = TrackVersion.from_sequence(sequence=sequence, version_name="test_add_track_version")
        track = Track(name="test_track").add_track_version(track_version=version)
        assert len(track.versions) == 1
        with pytest.raises(DuplicatedName):
            track = track.add_track_version(track_version=version)
        assert len(track.versions) == 1

    def test_delete_track_version(self, sequence):
        track = Track(name="test_track")
        version = TrackVersion.from_sequence(sequence=sequence, version_name="test_add_track_version")
        with pytest.raises(NoDataFound):
            track.delete_track_version(track_version=version)
        track.add_track_version(track_version=version)
        track.delete_track_version(track_version=version)
        assert len(track.versions) == 0

    def test_track_version_exists(self, sequence):
        track = Track(name="test_track")
        version = TrackVersion.from_sequence(sequence=sequence, version_name="test_add_track_version")
        assert not track.track_version_exists(identifier=version.name)
        assert not track.track_version_exists(identifier=version.name, existing_version=version)
        track = track.add_track_version(track_version=version)
        assert track.track_version_exists(identifier=version.name)
        assert not track.track_version_exists(identifier=version.name, existing_version=version)

    def test_get_default_version(self, sequence):
        version_name = "test_get_default_version"
        track = Track.from_sequence(
            name="TestTrack::test_get_default_version", version_name=version_name, sequence=sequence
        )
        assert track.get_default_version(raise_not_found=False).name == version_name
        track = Track(name="Empty")
        with pytest.raises(NoDataFound):
            track.get_default_version()
