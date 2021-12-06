from __future__ import annotations
import copy
from typing import List, Optional

from pydantic import BaseModel, PositiveInt

from src.app.utils.constants import CLR_NODE_START
from src.app.utils.constants import DEFAULT_SF2, DEFAULT_BANK, DEFAULT_PATCH

from src.app.model.event import Channel, MidiValue
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
    def from_sequence(cls, sequence: Sequence) -> TrackVersion:
        pass


class Track(BaseModel):
    name: str
    versions: List[TrackVersion]
    default_color: int = CLR_NODE_START.rgba()
    default_sf: str = DEFAULT_SF2
    default_bank: MidiValue = DEFAULT_BANK
    default_patch: MidiValue = DEFAULT_PATCH

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

    def get_default_version(self) -> TrackVersion:
        if self.versions:
            return self.versions[0]
        else:
            raise ValueError(
                f'Cannot get default track version. No version defined')


class TrackLoopItem(BaseModel):
    loop_track: Track
    loop_track_version: str
    loop_track_enabled: bool

    def get_track_version(self) -> TrackVersion:
        return self.loop_track.get_version(
            version_name=self.loop_track_version)

    def get_track_version_sequence(self) -> Sequence:
        return self.get_track_version().sequence


class Loop(BaseModel):
    name: str
    tracks: List[TrackLoopItem]
    checked: Optional[bool] = None

    def new_track(self, track: Track, enable: bool):
        self.tracks.append(TrackLoopItem(loop_track=track,
                                         loop_track_version=track.get_default_version().version_name,
                                         loop_track_enabled=enable))

    def get_sequence(self) -> Sequence:
        sequence: Optional[Sequence] = None
        tracks = [track for track in self.tracks if track.loop_track_enabled]
        if len(tracks):
            sequence = copy.deepcopy(
                tracks.pop(0).get_track_version().sequence)
            for track in tracks:
                sequence += track.get_track_version().sequence
        return sequence

    def set_single_track_version(self, track: Track,
                                 track_version: TrackVersion) -> None:
        for loop_item in self.tracks:
            if loop_item.loop_track == track:
                loop_item.loop_track_enabled = True
                loop_item.loop_track_version = track_version.version_name
            else:
                loop_item.loop_track_enabled = False


class Loops(BaseModel):
    loops: List[Loop]

    def get_next_sequence(self, loop_name: str) -> Optional[Sequence]:
        self.raise_not_implemented()
        return None

    def get_loop_by_name(self, loop_name: str) -> Loop:
        for loop in self.loops:
            if loop.name == loop_name:
                return loop
        raise ValueError(f'Cannot find loop by name {loop_name}')

    def get_sequence_by_loop_name(self, loop_name: str) -> Sequence:
        return self.get_loop_by_name(loop_name=loop_name).get_sequence()

    def get_first_loop_name(self) -> Optional[str]:
        self.raise_not_implemented()
        return None

    def set_checked_loop(self, loop: Loop):
        self.raise_not_implemented()

    def raise_not_implemented(self):
        raise NotImplementedError('Method not implemented in base class')


class CustomLoops(Loops):
    def get_checked_loop(self):
        for loop in self.loops:
            if loop.checked:
                return loop
        raise ValueError(
            f'Cannot find checked loop between {[loop.name for loop in self.loops]}')

    def set_checked_loop(self, loop: Loop):
        loop.checked = True
        for unchecked in [item for item in self.loops if item != loop]:
            unchecked.checked = False

    def get_next_sequence(self, loop_name: str) -> Optional[Sequence]:
        return self.get_checked_loop().get_sequence()

    def get_first_loop_name(self) -> Optional[str]:
        return self.get_checked_loop().name

    def get_loop_by_name(self, loop_name: str):
        return self.get_checked_loop()


class CompositionLoops(Loops):
    def get_next_sequence(self, loop_name: str) -> Optional[Sequence]:
        loop = self.get_loop_by_name(loop_name=loop_name)
        try:
            next_loop = self.loops[int(loop_name) + 1]
            return next_loop.get_sequence()
        except IndexError:
            return None

    def get_first_loop_name(self) -> Optional[str]:
        return self.loops[0].name if len(self.loops) > 0 else None
