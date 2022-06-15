from __future__ import annotations

import copy
from typing import Optional
from uuid import UUID

from pydantic import BaseModel

from src.app.model.composition import Compositions
from src.app.model.sequence import Sequence
from src.app.model.track import Track, Tracks
from src.app.model.types import Bpm, get_one
from src.app.model.variant import Variant, Variants, VariantType
from src.app.utils.exceptions import NoDataFound, NoItemSelected, OutOfVariants
from src.app.utils.notification import notify
from src.app.utils.properties import NotificationMessage, GuiAttr, MidiAttr


class ProjectVersion(BaseModel):
    name: str
    bpm: Bpm = GuiAttr.DEFAULT_BPM
    tracks: Tracks = Tracks()
    variants: Variants = Variants()
    compositions: Compositions = Compositions()

    def add_track(self, track: Track, enable: bool) -> ProjectVersion:
        self.tracks.add_track(track=track)
        self.variants.add_track(track=track, enable=enable)
        self.compositions.add_track(track=track, enable=enable)
        notify(message=NotificationMessage.TRACK_ADDED, track=track)
        return self

    # not tested
    def remove_track(self, track: Track) -> ProjectVersion:
        self.tracks.remove_track(track=track)
        self.variants.remove_track(track=track)
        self.compositions.remove_track(track=track)
        notify(message=NotificationMessage.TRACK_REMOVED, track=track)
        return self

    # not tested
    def change_track(self, track_id: int, new_track: Track) -> ProjectVersion:
        self.tracks.change_track(track_id=track_id, new_track=new_track)
        self.variants.change_track(track_id=track_id, new_track=new_track)
        self.compositions.change_track(track_id=track_id, new_track=new_track)
        notify(message=NotificationMessage.TRACK_CHANGED, track_id=track_id, new_track=new_track)
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

    def _get_compiled_sequence(self, variant_id: UUID, track: Track, include_defaults: bool = False) -> Sequence:
        variant = self.get_variant(variant_id=variant_id)
        version_id = variant.get_track_variant_item(track=track).version_id
        return track.get_version(identifier=version_id).get_sequence(include_defaults=include_defaults)

    def get_compiled_sequence(
        self, variant_id: UUID, single_track: Track = None, include_defaults: bool = False, raise_not_found: bool = True
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
                self._get_compiled_sequence(
                    variant_id=variant_id, track=tracks.pop(0), include_defaults=include_defaults
                )
            )
            for track in tracks:
                sequence += copy.deepcopy(
                    self._get_compiled_sequence(variant_id=variant_id, track=track, include_defaults=include_defaults)
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
    def init_from_tracks(cls, name: str, bpm: Bpm, tracks: Tracks) -> ProjectVersion:
        project_version = cls(name=name, bpm=bpm, tracks=tracks)
        project_version.add_single_variant(name=GuiAttr.DEFAULT_VERSION_NAME, selected=True, enable_all_tracks=True)
        composition = project_version.compositions.add_empty_composition(name=GuiAttr.DEFAULT_COMPOSITION)
        project_version.add_composition_variant(
            name="1", composition_name=composition.name, selected=True, enable_all_tracks=True
        )
        return project_version

    def get_next_free_channel(self):
        reserved = set()
        for track in self.tracks:
            for track_version in track.versions:
                reserved.add(track_version.channel)
        for channel in MidiAttr.CHANNELS:
            if channel not in reserved:
                return channel
        return None

    def get_first_track_version(self):
        track: Track = get_one(data=list(self.tracks), raise_on_empty=True)
        return track.get_default_version(raise_not_found=True)

    def track_exists(self, identifier: UUID | str, existing_track: Track = None) -> bool:
        track = self.tracks.get_track(identifier=identifier, raise_not_found=False)
        return track and track != existing_track
