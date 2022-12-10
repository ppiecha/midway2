from src.app.model.variant import Variants, Variant, VariantType, VariantItem


class TestVariant:
    def test_add_track(self, empty_composition_variant, track_c_major):
        variant = empty_composition_variant.add_track(track=track_c_major, enable=True)
        assert len(variant.items) == 1
        assert variant.items[0].version_id == track_c_major.get_default_version().id

    def test_remove_track(self, empty_composition_variant, track_c_major):
        variant = empty_composition_variant.add_track(track=track_c_major, enable=True)
        assert len(variant.items) == 1
        variant = variant.remove_track(track=track_c_major)
        assert len(variant.items) == 0

    def test_enabled(self, variant_c_major_composition):
        ids = variant_c_major_composition.get_enabled_tracks_ids()
        assert ids == [variant_c_major_composition.items[0].track_id]

    def test_scale_variant(self, empty_project_version, track_c_major):
        empty_project_version.add_track(track=track_c_major, enable=True)
        variant_item = VariantItem(
            track_id=track_c_major.id, version_id=track_c_major.get_default_version().id, enabled=True
        )
        variant = Variant(name="test scale", type=VariantType.SINGLE, selected=True, items=[variant_item])
        empty_project_version.variants.add_variant(variant=variant)
        assert len(list(empty_project_version.get_compiled_sequence(variant_id=variant.id).events())) == 16


class TestVariants:
    def test_get_next_variant(self, empty_composition_variant, variant_c_major_composition):
        variants = Variants(__root__=[empty_composition_variant, variant_c_major_composition])
        next_variant = variants.get_next_variant(variant_id=empty_composition_variant.id, repeat=False)
        assert next_variant.name == variant_c_major_composition.name
