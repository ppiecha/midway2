from src.app.model.project_version import ProjectVersion
from src.app.model.track import Tracks


def test_add_track(empty_project_version, track_c_major, empty_single_variant, empty_composition_variant):
    empty_project_version.variants.add_variant(variant=empty_single_variant)
    assert len(empty_project_version.variants) == 1
    empty_project_version.compositions.add_empty_composition(name="test_composition")
    assert len(empty_project_version.compositions) == 1
    empty_project_version.compositions[0].variants.add_variant(variant=empty_composition_variant)
    project_version = empty_project_version.add_track(track=track_c_major, enable=True)
    assert len(project_version.tracks) == 1
    assert project_version.tracks.get_track(identifier=track_c_major.id).id == track_c_major.id
    # assert project version get variants 0 sequence, composition 0 variant 0 seq equal track seq
    assert (
        project_version.get_compiled_sequence(variant_id=project_version.variants[0].id).dict()
        == track_c_major.get_default_version().get_sequence().dict()
    )
    assert (
        project_version.get_compiled_sequence(variant_id=project_version.compositions[0].variants[0].id).dict()
        == track_c_major.get_default_version().get_sequence().dict()
    )


def test_is_last_variant(track_c_major, bpm):
    tracks = Tracks(__root__=[track_c_major])
    project_version = ProjectVersion.init_from_tracks(name="test_is_last_variant", bpm=bpm, tracks=tracks)
    variant = project_version.add_single_variant(name="test_is_last_variant", selected=True, enable_all_tracks=True)
    assert project_version.is_last_variant(variant_id=variant.id, repeat=False)
    assert not project_version.is_last_variant(variant_id=variant.id, repeat=True)
