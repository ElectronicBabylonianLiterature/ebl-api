import pytest

from ebl.iiif.domain.image_formats import PAINTABLE_IMAGE_FORMATS, SVG, is_paintable
from ebl.iiif.domain.language_map import NO_LANGUAGE, LanguageMap


def test_of_uses_the_none_language_by_default():
    assert LanguageMap.of("K.1").to_dict() == {NO_LANGUAGE: ["K.1"]}


def test_of_accepts_an_explicit_language():
    assert LanguageMap.of("A fragment.", "en").to_dict() == {"en": ["A fragment."]}


def test_of_all_keeps_every_value_in_order():
    assert LanguageMap.of_all(["one", "two"], "en").to_dict() == {"en": ["one", "two"]}


def test_optional_returns_none_for_a_missing_value():
    assert LanguageMap.optional(None) is None


def test_optional_wraps_a_present_value():
    assert LanguageMap.optional("Obverse") == LanguageMap.of("Obverse")


def test_language_maps_are_values():
    assert LanguageMap.of("K.1") == LanguageMap.of("K.1")
    assert LanguageMap.of("K.1") != LanguageMap.of("K.2")


@pytest.mark.parametrize("mime_type", sorted(PAINTABLE_IMAGE_FORMATS))
def test_raster_formats_are_paintable(mime_type: str):
    assert is_paintable(mime_type)


@pytest.mark.parametrize("mime_type", [SVG, "application/pdf", "audio/mpeg", ""])
def test_other_formats_are_not_paintable(mime_type: str):
    assert not is_paintable(mime_type)
