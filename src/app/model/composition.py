from __future__ import annotations
from typing import List, Optional, Dict

from pydantic import BaseModel

from src.app.model.bar import Bar
from src.app.model.sequence import Sequence
from src.app.utils.constants import CHANNELS, DEFAULT_SF2, DEFAULT
from src.app.model.track import Track, TrackVersion
from src.app.model.loop import Loops, TrackLoopItem, Loop, CustomLoops, \
    LoopType
from src.app.model.event import Channel


class Composition(BaseModel):
    name: Optional[str]
    tracks: List[Track] = []
    loops: Optional[Dict[LoopType, Optional[Loops]]] = {}

    def insert_composition_loop(self, loop: Loop, loop_no: int):
        pass

    def delete_composition_loop(self, loop_no: int):
        pass

    def clear_composition_loops(self):
        self.loops[LoopType.composition] = Loops(loops=[])

    def get_custom_loop_by_name(self, loop_name: str,
                                raise_not_found: bool = True) \
            -> Optional[Loop]:
        if not (loops := self.get_loops(LoopType.custom)):
            if raise_not_found:
                raise ValueError(f'No custom loops in composition {self.name}')
            else:
                return None
        default = [loop for loop in loops.loops if loop.name == loop_name]
        if len(default) == 1:
            return default[0]
        elif len(default) > 1:
            raise ValueError(f'Found more than one custom loop with name '
                             f'{loop_name} in composition {self.name}')
        else:
            if raise_not_found:
                raise ValueError(
                    f'No default loop in custom loops in composition {self.name}')
            else:
                return None

    @property
    def default_loop(self, raise_not_found: bool = True) -> Loop:
        if self.get_custom_loop_by_name(loop_name=DEFAULT,
                                        raise_not_found=False) is None:
            self._update_default_loop()
        return self.get_custom_loop_by_name(loop_name=DEFAULT,
                                            raise_not_found=True)

    def _update_default_loop(self):
        if self.default_loop is None:
            loop = Loop(name=DEFAULT, tracks=[], checked=True)
            for track in self.tracks:
                version_name = track.get_default_version().version_name
                tli = TrackLoopItem(loop_track=track,
                                    loop_track_version=version_name,
                                    loop_track_enabled=True)
                loop.tracks.append(tli)
            self.loops[LoopType.custom] = CustomLoops(loops=[loop])

    def new_track(self, track: Track, enable: bool):
        if not self.track_name_exists(track_name=track.name,
                                      current_track=track,
                                      raise_not_found=False):
            self.tracks.append(track)
            for loops in self.loops.values():
                loops.new_track(track=track, enable=enable)

    def delete_track(self, track: Track):
        if self.track_name_exists(track_name=track.name,
                                  current_track=track,
                                  raise_not_found=True):
            self.tracks.remove(track)
            for loops in self.loops.values():
                loops.remove_track(track=track)

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

    def track_name_exists(self, track_name: str, current_track: Track,
                          raise_not_found: bool = False) -> bool:
        track = self.track_by_name(track_name=track_name,
                                   raise_not_found=raise_not_found)
        return track and track != current_track

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
    def from_tracks(cls, tracks: List[Track], name: str = '') -> Composition:
        composition = cls(name=name,
                          tracks=[],
                          loops={
                              LoopType.custom:
                                  CustomLoops(loops=[Loop(name=DEFAULT,
                                                          tracks=[],
                                                          checked=True)
                                                     ])
                          })
        for track in tracks:
            composition.new_track(track=track, enable=True)
        return composition

    @classmethod
    def from_sequence(cls, sequence: Sequence, name: str = '',
                      channel: Channel = 0, sf_name: str = DEFAULT_SF2) \
            -> Composition:
        version = TrackVersion.from_sequence(sequence=sequence,
                                             version_name=name,
                                             channel=channel,
                                             sf_name=sf_name)
        track = Track(name=name, versions=[version])
        return Composition.from_tracks(tracks=[track], name=name)

    @classmethod
    def from_bar(cls, bar: Bar, name: str = '', channel: Channel = 0,
                 sf_name: str = DEFAULT_SF2):
        sequence = Sequence(num_of_bars=1, bars={0: bar})
        track_version = TrackVersion(channel=channel, version_name=name,
                                     num_of_bars=1, sf_name=sf_name,
                                     sequence=sequence)
        track = Track(name=name, versions=[track_version])
        return Composition.from_tracks(tracks=[track], name=name)
