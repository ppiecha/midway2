from __future__ import annotations
from typing import List, Optional

from pydantic import BaseModel, PositiveInt

from src.app.utils.constants import CLR_NODE_START
from src.app.utils.constants import DEFAULT_SF2, DEFAULT_BANK, DEFAULT_PATCH

from src.app.model.event import Channel
from src.app.model.control import MidiValue
from src.app.model.sequence import Sequence


class TrackVersion(BaseModel):
    channel: Channel
    version_name: str
    num_of_bars: PositiveInt
    sf_name: str
    bank: MidiValue = DEFAULT_BANK
    patch: MidiValue = DEFAULT_PATCH
    sequence: Sequence

    @classmethod
    def from_sequence(cls, sequence: Sequence, channel: Channel = 0,
                      version_name: str = '', sf_name: str = DEFAULT_SF2) \
            -> TrackVersion:
        return cls(channel=channel, version_name=version_name,
                   num_of_bars=sequence.num_of_bars, sf_name=sf_name,
                   sequence=sequence)


class Track(BaseModel):
    name: str
    versions: List[TrackVersion]
    default_color: int = CLR_NODE_START.rgba()
    default_sf: str = DEFAULT_SF2
    default_bank: MidiValue = DEFAULT_BANK
    default_patch: MidiValue = DEFAULT_PATCH

    def add_track_version(self, track_version: TrackVersion):
        default = self.get_default_version(raise_not_found=False)
        if default and default.num_of_bars != track_version.num_of_bars:
            raise ValueError(f'Number of bars does not match. New '
                             f'{track_version.num_of_bars} existing '
                             f'{default.num_of_bars}')
        self.versions.append(track_version)

    def delete_track_version(self, track_version: TrackVersion):
        self.versions.remove(track_version)

    def track_version_by_name(self, track_version_name: str,
                              raise_not_found: bool = True) \
            -> Optional[TrackVersion]:
        for version in self.versions:
            if version.version_name == track_version_name:
                return version
        if raise_not_found:
            raise ValueError(f'Cannot find version {track_version_name} '
                             f'in versions {self.versions}')
        else:
            return None

    def track_version_exists(self, version_name: str,
                             current_version: TrackVersion) -> bool:
        version = self.track_version_by_name(track_version_name=version_name,
                                             raise_not_found=False)
        return version and version != current_version

    def get_version(self, version_name: str, raise_not_found: bool = False) \
            -> Optional[TrackVersion]:
        version = [version for version in self.versions if
                   version_name.lower() == version.version_name.lower()]
        if version:
            version, *rest = version
            return version
        else:
            if raise_not_found:
                raise ValueError(
                    f'Cannot find version {version_name} in track {self}')
            return None

    def get_default_version(self, raise_not_found: bool = True) \
            -> Optional[TrackVersion]:
        if self.versions:
            return self.versions[0]
        else:
            if raise_not_found:
                raise ValueError(
                    f'Cannot get default track version. No version defined')
            else:
                return None


