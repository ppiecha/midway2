from src.app.model.project_version import ProjectVersion
from src.app.model.track import Tracks
from src.app.utils.properties import GuiAttr


def test_scale_composition(track_c_major, bpm):
    tracks = Tracks(__root__=[track_c_major])
    project_version = ProjectVersion.init_from_tracks(name="test_scale_composition", bpm=bpm, tracks=tracks)
    composition = project_version.compositions.get_by_name(name=GuiAttr.DEFAULT_COMPOSITION)
    variant = composition.variants.get_first_variant()
    assert len(list(project_version.get_compiled_sequence(variant_id=variant.id).events())) == 16
