from uuid import UUID

from pydantic import BaseModel


class VariantItem(BaseModel):
    track_id: UUID
    version_id: UUID
    enabled: bool

    # def get_track_version(self) -> TrackVersion:
    #     return self.loop_track.get_version(version_name=self.loop_track_version)
    #
    # def get_track_version_sequence(self) -> Sequence:
    #     return self.get_track_version().sequence


# class Loop(BaseModel):
#     name: str
#     tracks: List[TrackLoopItem]
#     checked: Optional[bool] = None
#
#     def new_track(self, track: Track, enable: bool):
#         self.tracks.append(
#             TrackLoopItem(
#                 loop_track=track,
#                 loop_track_version=track.get_default_version().version_name,
#                 loop_track_enabled=enable,
#             )
#         )
#
#     def remove_track(self, track: Track):
#         self.tracks = [track_item for track_item in self.tracks if track_item.loop_track != track]
#
#     def get_compiled_sequence(self, include_defaults: bool = False) -> Sequence:
#         sequence: Optional[Sequence] = None
#         tracks = [track for track in self.tracks if track.loop_track_enabled]
#         if len(tracks):
#           sequence = copy.deepcopy(tracks.pop(0).get_track_version().get_sequence(include_defaults=include_defaults))
#             for track in tracks:
#                 sequence += track.get_track_version().get_sequence(include_defaults=include_defaults)
#         return sequence
#
#     def set_single_track_version(self, track: Track, track_version: TrackVersion) -> None:
#         for loop_item in self.tracks:
#             if loop_item.loop_track == track:
#                 loop_item.loop_track_enabled = True
#                 loop_item.loop_track_version = track_version.version_name
#             else:
#                 loop_item.loop_track_enabled = False
#
#     @classmethod
#     def from_tracks(cls, name: str, tracks: List[Track], checked: bool):
#         loop = cls(name=name, tracks=[], checked=checked)
#         for track in tracks:
#             loop.new_track(track=track, enable=checked)
#         return loop
#
#
# class Loops(BaseModel):
#     loops: List[Loop]
#
#     def get_next_loop(self, loop_name: str = "") -> Optional[Loop]:
#         raise NotImplementedError
#
#     def get_next_sequence(self, loop_name: str = "") -> Optional[Sequence]:
#         raise NotImplementedError
#
#     def get_loop_by_name(self, loop_name: str) -> Loop:
#         for loop in self.loops:
#             if loop.name == loop_name:
#                 return loop
#         raise ValueError(f"Cannot find loop by name {loop_name}")
#
#     def get_sequence_by_loop_name(self, loop_name: str) -> Sequence:
#         return self.get_loop_by_name(loop_name=loop_name).get_compiled_sequence()
#
#     def get_first_loop_name(self) -> Optional[str]:
#         raise NotImplementedError
#
#     def set_checked_loop(self, loop: Loop):
#         raise NotImplementedError
#
#     def get_total_num_of_bars(self) -> Optional[int]:
#         raise NotImplementedError
#
#     def new_track(self, track: Track, enable: bool):
#         for loop in self.loops:
#             loop.new_track(track=track, enable=enable)
#
#     def remove_track(self, track: Track):
#         for loop in self.loops:
#             loop.remove_track(track=track)
#
#
# class CustomLoops(Loops):
#     def get_checked_loop(self):
#         for loop in self.loops:
#             if loop.checked:
#                 return loop
#         raise ValueError(f"Cannot find checked loop between {[loop.name for loop in self.loops]}")
#
#     def set_checked_loop(self, loop: Loop):
#         loop.checked = True
#         for unchecked in [item for item in self.loops if item != loop]:
#             unchecked.checked = False
#
#     def get_next_sequence(self, loop_name: str = "") -> Optional[Sequence]:
#         return self.get_checked_loop().get_compiled_sequence()
#
#     def get_next_loop(self, loop_name: str = "") -> Optional[Loop]:
#         return self.get_checked_loop()
#
#     def get_first_loop_name(self) -> Optional[str]:
#         return self.get_checked_loop().name
#
#     def get_loop_by_name(self, loop_name: str):
#         return self.get_checked_loop()
#
#     def get_total_num_of_bars(self) -> Optional[int]:
#         return self.get_next_loop("").get_compiled_sequence().num_of_bars()
#
#
# class CompositionLoops(Loops):
#
#
#     def set_checked_loop(self, loop: Loop):
#         pass
#
#     def get_next_loop(self, loop_name: str = "") -> Optional[Loop]:
#         try:
#             loop_index = int(loop_name)
#         except ValueError as e:
#             raise ValueError(
#                 f"Cannot get next composition loop. " f"Wrong previous loop name {loop_name} {str(e)}"
#             ) from e
#         try:
#             next_loop = self.loops[loop_index + 1]
#             return next_loop
#         except IndexError:
#             return self.loops[int(GuiAttr.FIRST_COMPOSITION_LOOP)]
#
#     def get_next_sequence(self, loop_name: str = "") -> Optional[Sequence]:
#         next_loop = self.get_next_loop(loop_name=loop_name)
#         if next_loop is None:
#             return None
#         return next_loop.get_compiled_sequence()
#
#     def get_first_loop_name(self) -> Optional[str]:
#         if self.loops and len(self.loops) > 0:
#             return self.loops[0].name
#         raise ValueError("No loops in composition")
#
#     def get_total_num_of_bars(self) -> Optional[int]:
#         bars_total = 0
#         for loop in self.loops:
#             bars_total += loop.get_compiled_sequence().num_of_bars()
#         return bars_total
#
#     @classmethod
#     def from_list(cls, loop_lst: List[Loop]):
#         loops = []
#         for index, loop in enumerate(loop_lst):
#             loop_copy = loop.copy(deep=True)
#             loop_copy.name = str(index)
#             loops.append(loop_copy)
#         return cls(loops=loops)