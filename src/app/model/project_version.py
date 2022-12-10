from __future__ import annotations

import copy
from typing import Optional
from uuid import UUID, uuid4

from pydantic import BaseModel, Field

from src.app.model.composition import Compositions
from src.app.model.sequence import Sequence
from src.app.model.track import Track, Tracks, TrackVersion
from src.app.model.types import Bpm, get_one, Channel, Id, NumOfBars
from src.app.model.variant import Variant, Variants, VariantType
from src.app.utils.decorators import all_args_not_none
from src.app.utils.exceptions import NoDataFound, NoItemSelected, OutOfVariants
from src.app.utils.notification import notify
from src.app.utils.properties import NotificationMessage, GuiAttr, MidiAttr


class ProjectVersion(BaseModel):
    id: UUID = Field(default_factory=uuid4)
    name: str
    bpm: Bpm = GuiAttr.DEFAULT_BPM
    tracks: Tracks = Tracks()
    variants: Variants = Variants()
    compositions: Compositions = Compositions()

    def modify_project_version(self, project_version: ProjectVersion) -> ProjectVersion:
        notify(message=NotificationMessage.PROJECT_VERSION_CHANGED, old_version=self, new_version=project_version)
        self.name = project_version.name
        return self

    def add_track(self, track: Track, enable: bool) -> ProjectVersion:
        self.tracks.add_track(track=track)
        self.variants.add_track(track=track, enable=enable)
        self.compositions.add_track(track=track, enable=enable)
        notify(message=NotificationMessage.TRACK_ADDED, project_version=self, track=track)
        return self

    # not tested
    def change_track(self, project_version: ProjectVersion, track_id: Id, new_track: Track) -> ProjectVersion:
        self.tracks.change_track(track_id=track_id, new_track=new_track)
        notify(
            message=NotificationMessage.TRACK_CHANGED,
            project_version=project_version,
            track_id=track_id,
            new_track=new_track,
        )
        return self

    def remove_track(self, track: Track) -> ProjectVersion:
        self.remove_all_track_versions(track=track)
        self.tracks.remove_track(track=track)
        self.variants.remove_track(track=track)
        self.compositions.remove_track(track=track)
        notify(message=NotificationMessage.TRACK_REMOVED, project_version=self, track=track)
        return self

    def remove_all_tracks(self) -> ProjectVersion:
        for track in self.tracks:
            self.remove_track(track=track)
        return self

    def add_track_version(self, track: Track, track_version: TrackVersion) -> ProjectVersion:
        modified_track = self.tracks.get_track(identifier=track.name).add_track_version(track_version=track_version)
        notify(message=NotificationMessage.TRACK_VERSION_ADDED, track=modified_track, track_version=track_version)
        return self

    def remove_track_version(self, track: Track, track_version: TrackVersion) -> ProjectVersion:
        modified_track = self.tracks.get_track(identifier=track.name).delete_track_version(track_version=track_version)
        notify(message=NotificationMessage.TRACK_VERSION_REMOVED, track=modified_track, track_version=track_version)
        return self

    def remove_all_track_versions(self, track: Track) -> ProjectVersion:
        for track_version in track.versions:
            self.remove_track_version(track=track, track_version=track_version)
        return self

    def _get_variants(self, variant_id: UUID) -> Variants:
        if any(variant.id == variant_id for variant in self.variants):
            return self.variants
        for composition in self.compositions:
            if any(variant.id == variant_id for variant in composition.variants):
                return composition.variants
        raise NoDataFound(
            f"Cannot find variant id {variant_id} in project version {[variant.id for variant in self.variants]} "
            f"{[variant.id for composition in self.compositions for variant in composition.variants]}"
        )

    def get_next_variant(self, variant_id: UUID, repeat: bool, raise_on_last: bool = False) -> Optional[Variant]:
        variants = self._get_variants(variant_id=variant_id)
        if raise_on_last and self.is_last_variant(variant_id=variant_id, repeat=repeat):
            raise OutOfVariants(f"{variant_id} {variants}")
        return variants.get_next_variant(variant_id=variant_id, repeat=repeat)

    def is_last_variant(self, variant_id: UUID, repeat: bool) -> bool:
        variants = self._get_variants(variant_id=variant_id)
        return variants.is_last_variant(variant_id=variant_id, repeat=repeat)

    def get_variant(self, variant_id: UUID) -> Variant:
        variants = self._get_variants(variant_id=variant_id)
        return variants.get_variant(variant_id=variant_id)

    def _get_compiled_sequence(self, variant_id: UUID, track: Track, include_preset: bool = True) -> Sequence:
        variant = self.get_variant(variant_id=variant_id)
        version_id = variant.get_track_variant_item(track=track).version_id
        return track.get_version(identifier=version_id).get_sequence(include_preset=include_preset)

    def get_compiled_sequence(
        self, variant_id: UUID, single_track: Track = None, include_preset: bool = True, raise_not_found: bool = True
    ) -> Sequence:
        variant = self.get_variant(variant_id=variant_id)
        if single_track:
            tracks = [single_track]
        else:
            tracks = [track for track in self.tracks if track.id in variant.get_enabled_tracks_ids()]
        if raise_not_found and not tracks:
            raise NoItemSelected(f"No tracks selected in current variant {variant.name}")
        sequence = None
        if tracks:
            sequence = copy.deepcopy(
                self._get_compiled_sequence(variant_id=variant_id, track=tracks.pop(0), include_preset=include_preset)
            )
            for track in tracks:
                sequence += copy.deepcopy(
                    self._get_compiled_sequence(variant_id=variant_id, track=track, include_preset=include_preset)
                )
        return sequence

    def get_total_num_of_bars(self, variant_id: UUID) -> int:
        variant = self.get_variant(variant_id=variant_id)
        variants = self._get_variants(variant_id=variant_id)
        track = self.tracks.get_track(identifier=variant.get_first_track_id())
        if variant.type == VariantType.SINGLE:
            return self.get_compiled_sequence(variant_id=variant_id, single_track=track).num_of_bars()
        return sum(
            self.get_compiled_sequence(variant_id=variant.id, single_track=track).num_of_bars() for variant in variants
        )

    def add_single_variant(self, name: str, selected: bool, enable_all_tracks: bool) -> Variant:
        variant = Variant.from_tracks(
            name=name,
            type_=VariantType.SINGLE,
            tracks=self.tracks,
            selected=selected,
            enable_all_tracks=enable_all_tracks,
        )
        self.variants.add_variant(variant=variant)
        notify(message=NotificationMessage.SINGLE_VARIANT_ADDED, project_version=self, variant=variant)
        return variant

    def add_composition_variant(
        self, name: str, composition_name: str, selected: bool, enable_all_tracks: bool
    ) -> Variant:
        variant = Variant.from_tracks(
            name=name,
            type_=VariantType.COMPOSITION,
            tracks=self.tracks,
            selected=selected,
            enable_all_tracks=enable_all_tracks,
        )
        self.compositions.get_by_name(name=composition_name).variants.add_variant(variant=variant)
        return variant

    @classmethod
    def init_from_tracks(cls, name: str, bpm: Bpm, tracks: Tracks, add_to_composition: bool = True) -> ProjectVersion:
        project_version = cls(name=name, bpm=bpm, tracks=tracks)
        project_version.add_single_variant(name=GuiAttr.DEFAULT_VERSION_NAME, selected=True, enable_all_tracks=True)
        composition = project_version.compositions.add_empty_composition(name=GuiAttr.DEFAULT_COMPOSITION)
        if add_to_composition:
            project_version.add_composition_variant(
                name="1", composition_name=composition.name, selected=True, enable_all_tracks=True
            )
        return project_version

    def get_next_free_channel(self) -> Optional[Channel]:
        return get_next_free_channel(project_version=self)

    def get_first_track_version(self, track: Optional[Track]):
        if track is None:
            track: Track = get_one(data=list(self.tracks), raise_on_empty=True, raise_on_multiple=False)
        return track.get_default_version(raise_not_found=True)

    # def track_exists(self, identifier: UUID | str, existing_track: Track = None) -> bool:
    #     track = self.tracks.get_track(identifier=identifier, raise_not_found=False)
    #     return track and track != existing_track

    def is_new_track_name_valid(self, new_name: str, exclude_id: Optional[UUID] = None) -> bool:
        track = self.tracks.get_track(identifier=new_name, raise_not_found=False)
        if track and exclude_id:
            return track.id == exclude_id
        return track is None


@all_args_not_none
def has_tracks(project_version: ProjectVersion) -> bool:
    return len(project_version.tracks) > 0


def get_next_free_channel(project_version: ProjectVersion) -> Channel:
    if project_version:
        reserved = {track_version.channel for track in project_version.tracks for track_version in track.versions}
        for channel in MidiAttr.CHANNELS:
            if channel not in reserved:
                return channel
        return None
    return get_one(data=MidiAttr.CHANNELS, raise_on_multiple=False)


def get_num_of_bars(project_version: Optional[ProjectVersion]) -> NumOfBars:
    if project_version is None:
        return GuiAttr.DEFAULT_NUM_OF_BARS
    if not has_tracks(project_version=project_version):
        return GuiAttr.DEFAULT_NUM_OF_BARS
    return project_version.get_first_track_version(track=None).num_of_bars()
