import copy
from typing import List, Optional

from pydantic import BaseModel

from src.app.model.sequence import Sequence
from src.app.model.track import Track, TrackVersion


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
        self.tracks.append(
            TrackLoopItem(loop_track=track,
                          loop_track_version=track.get_default_version().version_name,
                          loop_track_enabled=enable))

    def remove_track(self, track: Track):
        self.tracks = [track_item for track_item in self.tracks
                       if track_item.loop_track != track]

    def get_compiled_sequence(self, include_defaults: bool = False) -> Sequence:
        # raise NotImplementedError
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

    @classmethod
    def from_tracks(cls, name: str, tracks: List[Track], checked: bool):
        loop = cls(name=name, tracks=[], checked=checked)
        for track in tracks:
            loop.new_track(track=track, enable=checked)
        return loop


class Loops(BaseModel):
    loops: List[Loop]

    def get_next_loop(self, loop_name: str = '') -> Optional[Loop]:
        self.raise_not_implemented()
        return None

    def get_next_sequence(self, loop_name: str = '') -> Optional[Sequence]:
        self.raise_not_implemented()
        return None

    def get_loop_by_name(self, loop_name: str) -> Loop:
        for loop in self.loops:
            if loop.name == loop_name:
                return loop
        raise ValueError(f'Cannot find loop by name {loop_name}')

    def get_sequence_by_loop_name(self, loop_name: str) -> Sequence:
        return self.get_loop_by_name(
            loop_name=loop_name).get_compiled_sequence()

    def get_first_loop_name(self) -> Optional[str]:
        self.raise_not_implemented()
        return None

    def set_checked_loop(self, loop: Loop):
        self.raise_not_implemented()

    def raise_not_implemented(self):
        raise NotImplementedError('Method not implemented')

    def get_total_num_of_bars(self) -> Optional[int]:
        self.raise_not_implemented()
        return None

    def new_track(self, track: Track, enable: bool):
        for loop in self.loops:
            loop.new_track(track=track, enable=enable)

    def remove_track(self, track: Track):
        for loop in self.loops:
            loop.remove_track(track=track)


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

    def get_next_sequence(self, loop_name: str = '') -> Optional[Sequence]:
        return self.get_checked_loop().get_compiled_sequence()

    def get_next_loop(self, loop_name: str = '') -> Optional[Loop]:
        return self.get_checked_loop()

    def get_first_loop_name(self) -> Optional[str]:
        return self.get_checked_loop().name

    def get_loop_by_name(self, loop_name: str):
        return self.get_checked_loop()

    def get_total_num_of_bars(self) -> Optional[int]:
        return self.get_next_loop('').get_compiled_sequence().num_of_bars


class CompositionLoops(Loops):
    def get_next_loop(self, loop_name: str = '') -> Optional[Loop]:
        try:
            next_loop = self.loops[int(loop_name) + 1]
            return next_loop
        except IndexError:
            return None

    def get_next_sequence(self, loop_name: str = '') -> Optional[Sequence]:
        next_loop = self.get_next_loop(loop_name=loop_name)
        if next_loop is None:
            return None
        else:
            return next_loop.get_compiled_sequence()

    def get_first_loop_name(self) -> Optional[str]:
        return self.loops[0].name if len(self.loops) > 0 else None

    def get_total_num_of_bars(self) -> Optional[int]:
        bars_total = 0
        for loop in self.loops:
            bars_total += loop.get_compiled_sequence().num_of_bars
        return bars_total
