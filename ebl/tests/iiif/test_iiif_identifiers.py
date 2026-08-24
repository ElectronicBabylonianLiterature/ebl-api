import pytest

from ebl.iiif.application.fragment_identity import ProvisionalMuseumNumberIdentity
from ebl.iiif.application.iiif_identifiers import (
    IiifIdentifierFactory,
    normalize_base_url,
)
from ebl.iiif.application.image_service import NoImageService
from ebl.tests.iiif.factories import BASE_URL, MEDIA_ID, identifiers
from ebl.transliteration.domain.museum_number import MuseumNumber

NUMBER = MuseumNumber.of("K.1")


@pytest.mark.parametrize(
    "base_url", ["https://api.example.org/", "https://api.example.org"]
)
def test_trailing_slashes_are_normalized(base_url: str):
    assert normalize_base_url(base_url) == BASE_URL


@pytest.mark.parametrize(
    "base_url",
    [
        "ftp://api.example.org",
        "api.example.org",
        "",
        "https:///path",
        "https://api.example.org?a=b",
        "https://api.example.org#fragment",
    ],
)
def test_invalid_base_urls_are_rejected(base_url: str):
    with pytest.raises(ValueError):
        normalize_base_url(base_url)


def test_manifest_identifier():
    assert identifiers().manifest(NUMBER) == f"{BASE_URL}/iiif/3/fragment/K.1/manifest"


def test_canvas_identifier_is_keyed_on_the_media_identity():
    assert (
        identifiers().canvas(NUMBER, MEDIA_ID)
        == f"{BASE_URL}/iiif/3/fragment/K.1/canvas/{MEDIA_ID}"
    )


def test_painting_page_and_annotation_hang_off_the_canvas():
    factory = identifiers()
    canvas = factory.canvas(NUMBER, MEDIA_ID)

    assert factory.painting_page(NUMBER, MEDIA_ID) == f"{canvas}/page/painting"
    assert (
        factory.painting_annotation(NUMBER, MEDIA_ID) == f"{canvas}/annotation/painting"
    )


def test_fragment_identifiers_containing_a_slash_are_encoded():
    assert "A%2FB.1" in identifiers().manifest(MuseumNumber.of("A/B.1"))


def test_media_identifiers_are_encoded():
    assert "a%2Fb" in identifiers().canvas(NUMBER, "a/b")


def test_an_empty_media_identifier_is_rejected():
    with pytest.raises(ValueError, match="must not be empty"):
        identifiers().canvas(NUMBER, "")


def test_absolute_builds_paths_from_the_configured_base():
    assert identifiers().absolute("/fragments/K.1") == f"{BASE_URL}/fragments/K.1"


def test_the_fragment_identity_is_exposed():
    factory = IiifIdentifierFactory(BASE_URL, ProvisionalMuseumNumberIdentity())

    assert isinstance(factory.fragment_identity, ProvisionalMuseumNumberIdentity)


def test_the_museum_number_identity_is_not_stable():
    assert ProvisionalMuseumNumberIdentity().is_stable() is False


def test_no_image_service_advertises_nothing():
    assert NoImageService().service_for(MEDIA_ID) is None
