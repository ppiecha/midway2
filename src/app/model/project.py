from typing import List

from pydantic import BaseModel

from src.app.model.project_version import ProjectVersion
from src.app.model.sequence import Sequence
from src.app.model.track import TrackVersion, Track, Tracks
from src.app.model.types import TrackType
from src.app.utils.properties import MidiAttr, GuiAttr


class Project(BaseModel):
    name: str
    versions: List[ProjectVersion] = []


def empty_project() -> Project:
    sequence = Sequence.from_num_of_bars(num_of_bars=GuiAttr.DEFAULT_NUM_OF_BARS)
    version = TrackVersion(
        channel=0, name=GuiAttr.DEFAULT_VERSION_NAME, sf_name=MidiAttr.DEFAULT_SF2, sequence=sequence
    )
    track = Track(name="Empty track", type=TrackType.VOICE, versions=[version])
    tracks = Tracks(__root__=[track])
    project_version = ProjectVersion.init_from_tracks(
        name="Default project version", bpm=GuiAttr.DEFAULT_BPM, tracks=tracks
    )
    return Project(name="New project", versions=[project_version])
