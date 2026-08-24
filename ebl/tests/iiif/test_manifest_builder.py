import attr
import pytest

from ebl.common.domain.scopes import Scope
from ebl.iiif.application.manifest_builder import ManifestBuilder, ManifestProvider
from ebl.iiif.application.manifest_sources import MetadataSource
from ebl.iiif.domain.language_map import LanguageMap
from ebl.iiif.domain.manifest import PRESENTATION_CONTEXT
from ebl.tests.iiif.factories import (
    ATTRIBUTION,
    BASE_URL,
    MEDIA_ID,
    OTHER_MEDIA_ID,
    RIGHTS,
    MissingImageService,
    fragment_source,
    identifiers,
    image_source,
    media_source,
)


@pytest.fixture
def builder():
    return ManifestBuilder(identifiers(), MissingImageService())


def test_a_public_fragment_yields_a_manifest(builder):
    manifest = builder.build(fragment_source())

    assert manifest is not None
    assert manifest.context == PRESENTATION_CONTEXT
    assert manifest.id == f"{BASE_URL}/iiif/3/fragment/K.1/manifest"
    assert manifest.label == LanguageMap.of("K.1")
    assert manifest.rights == RIGHTS


def test_a_restricted_fragment_yields_no_manifest(builder):
    fragment = fragment_source(authorized_scopes=[Scope.READ_CAIC_FRAGMENTS])

    assert builder.build(fragment) is None


def test_a_fragment_without_eligible_media_yields_no_manifest(builder):
    assert builder.build(fragment_source(media=[])) is None


def test_a_fragment_without_rights_yields_no_manifest(builder):
    assert builder.build(fragment_source(media=[media_source(rights=None)])) is None


def test_a_fragment_with_conflicting_terms_yields_no_manifest(builder):
    media = [media_source(MEDIA_ID), media_source(OTHER_MEDIA_ID, attribution="Other")]

    assert builder.build(fragment_source(media=media)) is None


def test_the_manifest_thumbnail_comes_from_the_primary_media(builder):
    media = [
        media_source(MEDIA_ID, sort_order=0, is_primary=False),
        media_source(
            OTHER_MEDIA_ID,
            sort_order=1,
            is_primary=True,
            thumbnail_image=image_source(
                f"{BASE_URL}/primary.jpg", width=240, height=180
            ),
        ),
    ]

    manifest = builder.build(fragment_source(media=media))

    assert [item.id for item in manifest.thumbnail] == [f"{BASE_URL}/primary.jpg"]


def test_the_first_canvas_is_used_when_no_media_is_primary(builder):
    media = [media_source(MEDIA_ID, is_primary=False)]

    manifest = builder.build(fragment_source(media=media))

    assert manifest.thumbnail == manifest.items[0].thumbnail


def test_the_required_statement_carries_the_attribution(builder):
    manifest = builder.build(fragment_source())

    assert manifest.required_statement.value == LanguageMap.of(ATTRIBUTION, "en")


def test_no_required_statement_without_an_attribution(builder):
    media = media_source(attribution=None)

    manifest = builder.build(fragment_source(media=[media]))

    assert manifest.required_statement is None


def test_metadata_summary_homepage_and_see_also_are_carried(builder):
    fragment = fragment_source(
        metadata=[MetadataSource("Script", "Neo-Assyrian")],
        summary="A fragment.",
        homepage_url="https://www.example.org/fragmentarium/K.1",
        record_url=f"{BASE_URL}/fragments/K.1",
    )

    manifest = builder.build(fragment)

    assert manifest.summary == LanguageMap.of("A fragment.", "en")
    assert manifest.metadata[0].value == LanguageMap.of("Neo-Assyrian")
    assert manifest.homepage[0].format == "text/html"
    assert manifest.see_also[0].format == "application/json"


def test_optional_manifest_links_are_omitted(builder):
    manifest = builder.build(fragment_source())

    assert manifest.homepage == ()
    assert manifest.see_also == ()
    assert manifest.metadata == []
    assert manifest.summary is None


def test_a_provider_is_attached_when_configured():
    builder = ManifestBuilder(
        identifiers(),
        MissingImageService(),
        ManifestProvider("https://www.example.org/", "eBL"),
    )

    manifest = builder.build(fragment_source())

    assert manifest is not None
    assert manifest.provider[0].label == LanguageMap.of("eBL", "en")


def test_no_provider_is_attached_by_default(builder):
    manifest = builder.build(fragment_source())

    assert manifest is not None
    assert manifest.provider == ()


def test_sources_are_immutable():
    media = media_source()

    assert attr.evolve(media, rights=None).rights is None
    assert media.rights == RIGHTS
