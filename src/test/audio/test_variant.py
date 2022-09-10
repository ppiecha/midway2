from src.app.model.project_version import ProjectVersion

from src.app.model.sequence import Sequence
from src.app.model.track import TrackVersion, Track, Tracks
from src.app.utils.properties import GuiAttr, MidiAttr


def test_play_single_variant(track_c_major, synth, bpm):
    tracks = Tracks(__root__=[track_c_major])
    project_version = ProjectVersion.init_from_tracks(name="test_play_single_variant", bpm=bpm, tracks=tracks)
    variant = project_version.add_single_variant(name="test_play_single_variant", selected=True, enable_all_tracks=True)
    synth.play(project_version=project_version, start_variant_id=variant.id)
    synth.wait_to_the_end()


def test_play_composition_variant(track_c_major, synth, bpm):
    variant_name = "test_play_composition_variant"
    tracks = Tracks(__root__=[track_c_major])
    project_version = ProjectVersion.init_from_tracks(name=variant_name, bpm=bpm, tracks=tracks)
    project_version.add_composition_variant(
        name=variant_name, composition_name=GuiAttr.DEFAULT_COMPOSITION, selected=True, enable_all_tracks=True
    )
    variant_id = (
        project_version.compositions.get_by_name(name=GuiAttr.DEFAULT_COMPOSITION).variants.get_first_variant().id
    )
    synth.play(project_version=project_version, start_variant_id=variant_id)
    synth.wait_to_the_end()


def test_play_compiled_single_variant(synth, bar_c_major_up, bar_c_major_down, bpm):
    s1 = Sequence.from_bars([bar_c_major_up, bar_c_major_down], overwrite_bar_nums=True)
    s2 = Sequence.from_bars([bar_c_major_down, bar_c_major_up], overwrite_bar_nums=True)
    v1 = TrackVersion.from_sequence(sequence=s1)
    v2 = TrackVersion.from_sequence(sequence=s2)
    t1 = Track(name="t1", versions=[v1])
    t2 = Track(name="t2", versions=[v2])
    tracks = Tracks(__root__=[t1, t2])
    project_version = ProjectVersion.init_from_tracks(name="test_play_compiled_loop", bpm=bpm, tracks=tracks)
    synth.play(
        project_version=project_version,
        start_variant_id=project_version.variants.get_first_variant().id,
    )
    synth.wait_to_the_end()


def test_play_compiled_sound_fonts(synth, bar_c_major_up, bar_c_major_down, bpm):
    s1 = Sequence.from_bars([bar_c_major_up, bar_c_major_down], overwrite_bar_nums=True)
    s2 = Sequence.from_bars([bar_c_major_down, bar_c_major_up], overwrite_bar_nums=True)
    v1 = TrackVersion(channel=0, name="v1", sequence=s1, sf_name=MidiAttr.DEFAULT_SF2, patch=7)
    v2 = TrackVersion(channel=0, name="v2", sequence=s2, sf_name=MidiAttr.DEFAULT_SF2_CHORIUM, patch=26)
    t1 = Track(name="t1", versions=[v1])
    t2 = Track(name="t2", versions=[v2])
    tracks = Tracks(__root__=[t1, t2])
    project_version = ProjectVersion.init_from_tracks(name="test_play_compiled_loop", bpm=bpm, tracks=tracks)
    compiled = project_version.get_compiled_sequence(variant_id=project_version.variants.get_first_variant().id)
    print(compiled)
    synth.play(
        project_version=project_version, start_variant_id=project_version.variants.get_first_variant().id, bpm=50
    )
    synth.wait_to_the_end()
