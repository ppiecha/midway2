from __future__ import annotations
from typing import List, Optional

from pydantic import BaseModel, PositiveInt

from src.app.model.bar import Bar

from src.app.model.event import Event, EventType, Preset
from src.app.model.types import Channel, MidiValue, MidiBankValue
from src.app.model.sequence import Sequence
from src.app.utils.properties import Color, MidiAttr


class TrackVersion(BaseModel):
    channel: Channel
    version_name: str = ""
    sf_name: str
    bank: MidiBankValue = MidiAttr.DEFAULT_BANK
    patch: MidiValue = MidiAttr.DEFAULT_PATCH
    sequence: Sequence

    def num_of_bars(self) -> PositiveInt:
        return self.sequence.num_of_bars()

    @classmethod
    def from_sequence(
        cls,
        sequence: Sequence,
        channel: Channel = 0,
        version_name: str = "",
        sf_name: str = MidiAttr.DEFAULT_SF2,
    ) -> TrackVersion:
        return cls(
            channel=channel,
            version_name=version_name,
            num_of_bars=sequence.num_of_bars,
            sf_name=sf_name,
            sequence=sequence,
        )

    def get_sequence(self, include_defaults: bool = False) -> Sequence:
        if include_defaults:
            bars: List[Bar] = [bar for bar in self.sequence.bars.values()]
            if bars:
                first_bar, *rest = bars
                event = Event(
                    type=EventType.PROGRAM,
                    channel=self.channel,
                    beat=0,
                    preset=Preset(sf_name=self.sf_name, bank=self.bank, patch=self.patch),
                )
                first_bar.add_event(event=event)
                return Sequence.from_bars(bars=bars)
            else:
                raise ValueError(f"No bars in sequence {self.sequence}")
        else:
            return self.sequence


class RhythmTrackVersion(TrackVersion):
    channel: Channel = MidiAttr.DRUM_CHANNEL
    bank: MidiValue = MidiAttr.DRUM_BANK


class Track(BaseModel):
    name: str
    versions: List[TrackVersion]
    default_color: int = Color.NODE_START.rgba()
    default_sf: str = MidiAttr.DEFAULT_SF2
    default_bank: MidiValue = MidiAttr.DEFAULT_BANK
    default_patch: MidiValue = MidiAttr.DEFAULT_PATCH

    def add_track_version(self, track_version: TrackVersion):
        default = self.get_default_version(raise_not_found=False)
        if default and default.num_of_bars != track_version.num_of_bars:
            raise ValueError(
                f"Number of bars does not match. New " f"{track_version.num_of_bars} existing " f"{default.num_of_bars}"
            )
        self.versions.append(track_version)

    def delete_track_version(self, track_version: TrackVersion):
        self.versions.remove(track_version)

    def track_version_by_name(self, track_version_name: str, raise_not_found: bool = True) -> Optional[TrackVersion]:
        for version in self.versions:
            if version.version_name == track_version_name:
                return version
        if raise_not_found:
            raise ValueError(f"Cannot find version {track_version_name} " f"in versions {self.versions}")
        else:
            return None

    def track_version_exists(self, version_name: str, current_version: TrackVersion) -> bool:
        version = self.track_version_by_name(track_version_name=version_name, raise_not_found=False)
        return version and version != current_version

    def get_version(self, version_name: str, raise_not_found: bool = False) -> Optional[TrackVersion]:
        version = [version for version in self.versions if version_name == version.version_name]
        if version:
            if len(version) > 1:
                raise ValueError(f"Found more than one version with name " f"{version_name} in track {self.name}")
            else:
                version, *rest = version
                return version
        else:
            if raise_not_found:
                raise ValueError(f"Cannot find version {version_name} in track {self}")
            return None

    def get_default_version(self, raise_not_found: bool = True) -> Optional[TrackVersion]:
        if self.versions:
            return self.versions[0]
        else:
            if raise_not_found:
                raise ValueError(f"Cannot get default track version. No version defined")
            else:
                return None


class RhythmDrumTrack(Track):
    versions: List[RhythmTrackVersion]
