from __future__ import annotations

import copy
from collections.abc import Iterator
from typing import List, Optional
from uuid import UUID, uuid4

from pydantic import BaseModel, PositiveInt, Field

from src.app.model.bar import Bar
from src.app.model.event import EventType
from src.app.model.sequence import Sequence
from src.app.model.types import Channel, MidiValue, MidiBankValue, get_one, TrackType, Preset, Id
from src.app.utils.exceptions import DuplicatedName, NoDataFound
from src.app.utils.properties import Color, MidiAttr


class TrackVersion(BaseModel):
    channel: Channel
    id: UUID = Field(default_factory=uuid4)
    name: str
    sf_name: str
    bank: MidiBankValue = MidiAttr.DEFAULT_BANK
    patch: MidiValue = MidiAttr.DEFAULT_PATCH
    sequence: Sequence

    def preset(self):
        if any(item is None for item in (self.sf_name, self.bank, self.patch)):
            raise RuntimeError(f"Not all preset parts defined {(self.sf_name, self.bank, self.patch)}")
        return Preset(sf_name=self.sf_name, bank=self.bank, patch=self.patch)

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
            name=version_name,
            num_of_bars=sequence.num_of_bars,
            sf_name=sf_name,
            sequence=sequence,
        )

    def get_sequence(self, include_preset: bool = True) -> Sequence:
        if include_preset:
            last_preset = None
            bars: List[Bar] = []
            for old_bar in list(self.sequence):
                new_bar: Bar = copy.deepcopy(old_bar)
                new_bar.clear()
                for event in old_bar.events(deep_copy=True):
                    match event.type:
                        case EventType.NOTE:
                            if last_preset is None:
                                last_preset = self.preset()
                            event.preset = last_preset
                            new_bar.add_event(event=event)
                        case EventType.PROGRAM:
                            last_preset = event.preset
                        case _:
                            new_bar.add_event(event=event)
                bars.append(new_bar)
            return Sequence.from_bars(bars=bars)
        return self.sequence


class RhythmTrackVersion(TrackVersion):
    channel: Channel = MidiAttr.DRUM_CHANNEL
    bank: MidiValue = MidiAttr.DRUM_BANK


class Track(BaseModel):
    id: UUID = Field(default_factory=uuid4)
    name: str
    type: TrackType = TrackType.VOICE
    versions: List[TrackVersion] = []
    default_color: int = Color.NODE_START.rgba()
    default_sf: str = MidiAttr.DEFAULT_SF2
    default_bank: MidiValue = MidiAttr.DEFAULT_BANK
    default_patch: MidiValue = MidiAttr.DEFAULT_PATCH

    def __iter__(self):
        return iter(self.versions)

    def __getitem__(self, item):
        return self.versions[item]

    def change_track(self, track: Track) -> Track:
        self.name = track.name
        self.type = track.type
        self.default_color = track.default_color
        self.default_sf = track.default_sf
        self.default_bank = track.default_bank
        self.default_patch = track.default_patch
        return self

    def get_version(self, identifier: UUID | str, raise_not_found: bool = True) -> Optional[TrackVersion]:
        match identifier:
            case UUID() as uuid:
                return get_one(
                    data=[version for version in self.versions if version.id == uuid], raise_on_empty=raise_not_found
                )
            case str() as name:
                return get_one(
                    data=[version for version in self.versions if version.name == name], raise_on_empty=raise_not_found
                )
            case _:
                raise TypeError(f"Wrong type {type(identifier)}")

    def add_track_version(self, track_version: TrackVersion, raise_on_duplicate: bool = True) -> Track:
        if raise_on_duplicate and any(version.name == track_version.name for version in self.versions):
            raise DuplicatedName(
                f"Version with name {track_version.name} already exists in track {self.name}. "
                f"Current versions {[version.name for version in self.versions]}"
            )
        default = self.get_default_version(raise_not_found=False)
        if default and default.num_of_bars() != track_version.num_of_bars():
            raise ValueError(
                f"Number of bars does not match. New "
                f"{track_version.num_of_bars()} existing "
                f"{default.num_of_bars()}"
            )
        self.versions.append(track_version)
        return self

    def delete_track_version(self, track_version: TrackVersion, raise_not_exists: bool = True) -> Track:
        if self.track_version_exists(identifier=track_version.name):
            self.versions.remove(track_version)
        elif raise_not_exists:
            raise NoDataFound(f"Cannot find version {track_version.name} in track {self}")
        return self

    def track_version_exists(self, identifier: UUID | str, existing_version: TrackVersion = None) -> bool:
        version = self.get_version(identifier=identifier, raise_not_found=False)
        return version and version != existing_version

    def is_new_version_name_valid(self, new_name: str, exclude_id: Optional[UUID] = None) -> bool:
        version = self.get_version(identifier=new_name, raise_not_found=False)
        if version and exclude_id:
            return version.id == exclude_id
        return version is None

    def get_default_version(self, raise_not_found: bool = True) -> Optional[TrackVersion]:
        return get_one(data=self.versions, raise_on_empty=raise_not_found, raise_on_multiple=False)

    @classmethod
    def from_sequence(
        cls,
        sequence: Sequence,
        name: str = "",
        channel: Channel = 0,
        version_name: str = "",
        sf_name: str = MidiAttr.DEFAULT_SF2,
    ):
        return cls(
            name=name,
            versions=[
                TrackVersion.from_sequence(
                    sequence=sequence, channel=channel, version_name=version_name, sf_name=sf_name
                )
            ],
        )


class RhythmDrumTrack(Track):
    versions: List[RhythmTrackVersion]


class Tracks(BaseModel):
    __root__: List[Track] = []

    def __iter__(self) -> Iterator[Track]:
        return iter(self.__root__)

    def __getitem__(self, item) -> Track:
        return self.__root__[item]

    def __len__(self):
        return len(self.__root__)

    def add_track(self, track: Track, raise_on_duplicate: bool = True) -> Tracks:
        if raise_on_duplicate and any(t.name == track.name for t in self.__root__):
            raise DuplicatedName(f"Track with name {track.name} already exists")
        self.__root__.append(track)
        return self

    def change_track(self, track_id: Id, new_track: Track) -> Tracks:
        self.get_track(identifier=track_id).change_track(track=new_track)
        return self

    def remove_track(self, track: Track) -> Tracks:
        if not any(t.name == track.name for t in self.__root__):
            raise NoDataFound(f"Cannot remove track {track.name}. Not found")
        self.__root__ = [t for t in self.__root__ if t.name != track.name]
        return self

    def get_track(self, identifier: Id, raise_not_found: bool = True) -> Optional[Track]:
        match identifier:
            case UUID() as uuid:
                return get_one(
                    data=[track for track in self.__root__ if track.id == uuid], raise_on_empty=raise_not_found
                )
            case str() as name:
                return get_one(
                    data=[track for track in self.__root__ if track.name == name], raise_on_empty=raise_not_found
                )
            case _:
                raise TypeError(f"Wrong type {type(identifier)}")

    @classmethod
    def from_tracks(cls, tracks: List[Track]) -> Tracks:
        return cls(__root__=tracks)
