from __future__ import annotations

from collections.abc import Iterator
from enum import Enum
from typing import List, Optional
from uuid import UUID, uuid4

from pydantic import BaseModel, Field

from src.app.model.track import Track, Tracks, TrackVersion
from src.app.model.types import get_one
from src.app.utils.exceptions import NoDataFound


class VariantType(str, Enum):
    SINGLE = "single"
    COMPOSITION = "composition"


class VariantItem(BaseModel):
    id: UUID = Field(default_factory=uuid4)
    track_id: UUID
    version_id: UUID
    enabled: bool


class Variant(BaseModel):
    name: str
    id: UUID = Field(default_factory=uuid4)
    type: VariantType
    selected: bool
    items: List[VariantItem]

    def __iter__(self) -> Iterator[VariantItem]:
        return iter(self.items)

    def __getitem__(self, item) -> VariantItem:
        return self.items[item]

    def __len__(self):
        return len(self.items)

    def add_track(self, track: Track, enable: bool) -> Variant:
        self.items.append(VariantItem(track_id=track.id, version_id=track.get_default_version().id, enabled=enable))
        return self

    def remove_track(self, track: Track) -> Variant:
        self.items = [item for item in self.items if item.track_id != track.id]
        return self

    def get_track_variant_item(self, track: Track) -> VariantItem:
        items = [item for item in self.items if item.track_id == track.id]
        return get_one(data=items, raise_on_empty=True)

    def get_first_track_id(self) -> UUID:
        return get_one(self.items, raise_on_empty=True, raise_on_multiple=False).track_id

    def is_track_enabled(self, track: Track):
        item = self.get_track_variant_item(track=track)
        return item.enabled

    def get_enabled_tracks_ids(self) -> List[UUID]:
        return [item.track_id for item in self.items if item.enabled]

    def get_track_version_id(self, track: Track) -> Optional[UUID]:
        return self.get_track_variant_item(track=track).version_id if self.is_track_enabled(track=track) else None

    def set_track_version(self, track: Track, version: TrackVersion):
        item = self.get_track_variant_item(track=track)
        item.version_id = version.id

    def set_track_enabled(self, track: Track, enabled: bool):
        item = self.get_track_variant_item(track=track)
        item.enabled = enabled

    @classmethod
    def from_tracks(
        cls, name: str, type_: VariantType, tracks: Tracks, selected: bool, enable_all_tracks: bool
    ) -> Variant:
        variant = cls(name=name, type=type_, selected=selected, items=[])
        for track in tracks:
            variant.add_track(track=track, enable=enable_all_tracks)
        return variant


class Variants(BaseModel):
    __root__: List[Variant] = []

    def __iter__(self) -> Iterator[Variant]:
        return iter(self.__root__)

    def __getitem__(self, item) -> Variant:
        return self.__root__[item]

    def __len__(self):
        return len(self.__root__)

    def get_variant(self, variant_id: UUID) -> Variant:
        variants = [variant for variant in self if variant.id == variant_id]
        return get_one(data=variants, raise_on_empty=True)

    def get_next_variant(self, variant_id: UUID, repeat: bool) -> Optional[Variant]:
        variant = self.get_variant(variant_id=variant_id)
        if variant.type == VariantType.SINGLE:
            return variant if repeat else None
        try:
            variant_index = self.__root__.index(variant)
            next_variant_index = None
            if variant_index + 1 < len(self):
                next_variant_index = variant_index + 1
            else:
                if repeat:
                    next_variant_index = 0
            return self[next_variant_index] if next_variant_index else None
        except ValueError as e:
            raise NoDataFound(
                f"Cannot find variant {variant.name} in variants {[variant.name for variant in self]}"
            ) from e

    def is_last_variant(self, variant_id: UUID, repeat: bool) -> bool:
        return self.get_next_variant(variant_id=variant_id, repeat=repeat) is None

    def add_variant(self, variant: Variant) -> Variants:
        self.__root__.append(variant)
        return self

    def remove_variant(self, variant: Variant) -> Variants:
        self.__root__.remove(variant)
        return self

    def add_track(self, track: Track, enable: bool):
        for variant in self:
            variant.add_track(track=track, enable=enable)

    def remove_track(self, track: Track):
        for variant in self:
            variant.remove_track(track=track)

    def get_first_variant(self) -> Variant:
        return get_one(list(self), raise_on_empty=True, raise_on_multiple=False)
