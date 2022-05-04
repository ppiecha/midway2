from typing import List, Optional

from pydantic import BaseModel, PositiveInt

from src.app.model.composition import Composition
from src.app.model.sequence import Sequence
from src.app.model.track import TrackVersion, Track
from src.app.model.types import Bpm
from src.app.utils.properties import MidiAttr


class Project(BaseModel):
    name: str
    bpm: Bpm
    compositions: List[Composition]

    def num_of_bars(self) -> PositiveInt:
        if not self.compositions:
            raise ValueError(f"List of compositions is empty {self.compositions}")
        return self.compositions[0].num_of_bars()

    def composition_by_name(self, composition_name: str, raise_not_found: bool = True) -> Optional[Composition]:
        for composition in self.compositions:
            if composition.name == composition_name:
                return composition
        if raise_not_found:
            raise ValueError(f"Cannot find name {composition_name} in compositions {self.compositions}")
        return None

    def delete_composition(self, composition: Composition):
        self.compositions.remove(composition)


def simple_project() -> Project:
    track_version = TrackVersion(
        channel=100,
        version_name="Bass 0",
        sf_name=MidiAttr.DEFAULT_SF2,
        sequence=Sequence.from_num_of_bars(num_of_bars=8),
    )
    return Project(
        name="Simple project",
        bpm=90,
        compositions=[
            Composition(
                name="First composition",
                tracks=[
                    Track(name="Bass", current_version="Default", versions=[track_version]),
                ],
            ),
        ],
    )


def empty_project() -> Project:
    track_version = TrackVersion(
        channel=100,
        version_name="Bass 0",
        sf_name=MidiAttr.DEFAULT_SF2,
        sequence=Sequence.from_num_of_bars(num_of_bars=4),
    )
    track_version1 = TrackVersion(
        channel=2,
        version_name="Version 1",
        sf_name=MidiAttr.DEFAULT_SF2,
        sequence=Sequence.from_num_of_bars(num_of_bars=4),
    )
    track_version2 = TrackVersion(
        channel=2,
        version_name="Version 2",
        sf_name=MidiAttr.DEFAULT_SF2,
        sequence=Sequence.from_num_of_bars(num_of_bars=4),
    )
    return Project(
        name="Sample project",
        bpm=90,
        compositions=[
            Composition(
                name="Default",
                tracks=[
                    Track(name="Bass", current_version="Default", versions=[track_version]),
                    Track(
                        name="Guitar",
                        current_version="Default",
                        versions=[track_version1],
                    ),
                ],
            ),
            Composition(
                name="Second",
                tracks=[
                    Track(
                        name="Second track",
                        current_version="Version 0",
                        versions=[track_version],
                    ),
                    Track(
                        name="Third track",
                        current_version="Version 2",
                        versions=[track_version1, track_version2],
                    ),
                ],
            ),
        ],
    )
