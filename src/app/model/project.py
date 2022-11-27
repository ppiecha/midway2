from __future__ import annotations
from typing import List, Iterator

from pydantic import BaseModel

from src.app.model.project_version import ProjectVersion
from src.app.model.sequence import Sequence
from src.app.model.track import TrackVersion, Track, Tracks
from src.app.model.types import TrackType, get_one
from src.app.utils.notification import notify
from src.app.utils.properties import MidiAttr, GuiAttr, NotificationMessage


class Project(BaseModel):
    name: str
    versions: List[ProjectVersion] = []

    def __iter__(self) -> Iterator[ProjectVersion]:
        return iter(self.versions)

    def __getitem__(self, item) -> ProjectVersion:
        return self.versions[item]

    def __len__(self):
        return len(self.versions)

    def get_version_by_name(self, version_name: str) -> ProjectVersion:
        return get_one(data=[version for version in self if version.name == version_name], raise_on_empty=True)

    def delete_project_version(self, project_version: ProjectVersion):
        self.versions.remove(project_version)

    def modify_project(self, project: Project):
        self.name = project.name
        notify(message=NotificationMessage.PROJECT_CHANGED, project=project)


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
