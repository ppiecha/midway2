from typing import List, Optional, Dict

from pydantic import BaseModel

from src.app.model.bar import Bar
from src.app.model.sequence import Sequence
from src.app.utils.constants import CHANNELS, DEFAULT_SF2
from src.app.model.track import Track, Loops, TrackVersion
from src.app.model.event import LoopType, Channel


class Composition(BaseModel):
    name: Optional[str]
    tracks: List[Track] = []
    loops: Optional[Dict[LoopType, Optional[Loops]]] = {}

    def delete_track(self, track: Track):
        self.tracks.remove(track)

    def get_next_free_channel(self):
        reserved = set()
        for track in self.tracks:
            for track_version in track.versions:
                reserved.add(track_version.channel)
        for channel in CHANNELS:
            if channel not in reserved:
                return channel
        return None

    def get_loops(self, loop_type: LoopType) -> Loops:
        return self.loops.get(loop_type, [])

    def track_by_name(self, track_name: str, raise_not_found: bool = True) -> \
    Optional[Track]:
        for track in self.tracks:
            if track.name == track_name:
                return track
        if raise_not_found:
            raise ValueError(
                f'Cannot find name {track_name} in tracks {self.tracks}')
        else:
            return None

    def track_name_exists(self, track_name: str, current_track: Track) -> bool:
        track = self.track_by_name(track_name=track_name,
                                   raise_not_found=False)
        return track and track != current_track

    def new_track(self, track: Track, enable: bool):
        self.tracks.append(track)
        for loop_type, loops in self.loops.items():
            for loop in loops.loops:
                loop.new_track(track=track, enable=enable)

    def get_first_track_version(self) -> Optional[TrackVersion]:
        if self.tracks:
            track = self.tracks[0]
            return track.get_default_version()
        else:
            return None

    def get_first_track(self) -> Optional[Track]:
        if self.tracks:
            return self.tracks[0]
        else:
            return None

    @classmethod
    def from_bar(cls, bar: Bar, name: str = '', channel: Channel = 0,
                 sf_name: str = DEFAULT_SF2):
        sequence = Sequence(num_of_bars=1, bars={0: bar})
        track_version = TrackVersion(channel=channel, version_name=name,
                                     num_of_bars=1, sf_name=sf_name,
                                     sequence=sequence)
        track = Track(name=name, versions=[track_version])
        return cls(tracks=[track])


