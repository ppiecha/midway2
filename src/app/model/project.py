from typing import Dict, List, Optional

from pydantic import BaseModel, PositiveInt

from src.app.backend.synth_config import DEFAULT_SF2
from src.app.model.composition import Composition
from src.app.model.sequence import Sequence
from src.app.model.track import TrackVersion, Track
from src.app.model.types import Bpm


class Project(BaseModel):
    name: str
    bpm: Bpm
    num_of_bars: PositiveInt
    compositions: List[Composition]

    def composition_by_name(self, composition_name: str,
                            raise_not_found: bool = True) -> Optional[
        Composition]:
        for composition in self.compositions:
            if composition.name == composition_name:
                return composition
        if raise_not_found:
            raise ValueError(
                f'Cannot find name {composition_name} in compositions {self.compositions}')
        else:
            return None

    def delete_composition(self, composition: Composition):
        self.compositions.remove(composition)


def sample_project() -> Project:
    track_version = TrackVersion(channel=1, version_name='Bass 0',
                                 num_of_bars=4, sf_name=DEFAULT_SF2,
                                 sequence=Sequence(num_of_bars=4))
    track_version1 = TrackVersion(channel=2, version_name='Version 1',
                                  num_of_bars=4, sf_name=DEFAULT_SF2,
                                  sequence=Sequence(num_of_bars=4))
    track_version2 = TrackVersion(channel=2, version_name='Version 2',
                                  num_of_bars=4, sf_name=DEFAULT_SF2,
                                  sequence=Sequence(num_of_bars=4))
    return Project(name="Sample project", bpm=90, num_of_bars=4,
                   compositions=[Composition(name="Default",
                                             tracks=[Track(name="Bass",
                                                           current_version="Default",
                                                           versions=[
                                                               track_version]),
                                                     Track(name="Guitar",
                                                           current_version="Default",
                                                           versions=[
                                                               track_version1])
                                                     ]
                                             ),
                                 Composition(name="Second",
                                             tracks=[Track(name="Second track",
                                                           current_version="Version 0",
                                                           versions=[
                                                               track_version]),
                                                     Track(name="Third track",
                                                           current_version="Version 2",
                                                           versions=[
                                                               track_version1,
                                                               track_version2])
                                                     ]
                                             )
                                 ])
