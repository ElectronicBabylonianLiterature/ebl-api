import pytest

from ebl.iiif.application.image_service import LEVEL_TWO
from ebl.iiif.application.manifest_builder import ManifestBuilder
from ebl.iiif.domain.canvas import PAINTING_MOTIVATION
from ebl.iiif.domain.language_map import LanguageMap
from ebl.tests.iiif.factories import (
    BASE_URL,
    MEDIA_ID,
    OTHER_MEDIA_ID,
    RIGHTS,
    MissingImageService,
    StubImageService,
    fragment_source,
    identifiers,
    image_source,
    media_source,
    rendering_source,
)


@pytest.fixture
def builder():
    return ManifestBuilder(identifiers(), MissingImageService())


def test_one_eligible_media_item_becomes_one_canvas(builder):
    media = [media_source(MEDIA_ID), media_source(OTHER_MEDIA_ID, sort_order=1)]

    manifest = builder.build(fragment_source(media=media))

    assert len(manifest.items) == 2


def test_canvases_follow_the_media_sort_order(builder):
    media = [
        media_source(OTHER_MEDIA_ID, sort_order=1, label="Reverse"),
        media_source(MEDIA_ID, sort_order=0, label="Obverse"),
    ]

    manifest = builder.build(fragment_source(media=media))

    assert [canvas.label for canvas in manifest.items] == [
        LanguageMap.of("Obverse"),
        LanguageMap.of("Reverse"),
    ]


def test_canvas_identity_incorporates_the_media_identity(builder):
    manifest = builder.build(fragment_source())

    assert manifest.items[0].id.endswith(f"/canvas/{MEDIA_ID}")


def test_canvas_dimensions_come_from_the_authoritative_representation(builder):
    canvas = builder.build(fragment_source()).items[0]

    assert (canvas.width, canvas.height) == (4000, 3000)


def test_the_painting_body_keeps_its_own_dimensions(builder):
    body = builder.build(fragment_source()).items[0].items[0].items[0].body

    assert (body.width, body.height) == (2000, 1500)
    assert body.format == "image/jpeg"


def test_the_painting_annotation_targets_its_canvas(builder):
    canvas = builder.build(fragment_source()).items[0]
    annotation = canvas.items[0].items[0]

    assert annotation.motivation == PAINTING_MOTIVATION
    assert annotation.target == canvas.id
    assert annotation.id == f"{canvas.id}/annotation/painting"
    assert canvas.items[0].id == f"{canvas.id}/page/painting"


def test_no_image_service_is_advertised_when_none_exists(builder):
    manifest = builder.build(fragment_source())

    assert manifest.items[0].items[0].items[0].body.service == ()


def test_an_image_service_is_attached_when_one_exists():
    builder = ManifestBuilder(identifiers(), StubImageService())
    manifest = builder.build(fragment_source())

    assert manifest is not None
    service = manifest.items[0].items[0].items[0].body.service

    assert [item.id for item in service] == [f"{BASE_URL}/iiif/3/image/{MEDIA_ID}"]
    assert service[0].profile == LEVEL_TWO


def test_an_svg_original_is_offered_as_a_rendering(builder):
    media = media_source(rendering=rendering_source())

    rendering = builder.build(fragment_source(media=[media])).items[0].rendering

    assert [item.format for item in rendering] == ["image/svg+xml"]
    assert rendering[0].id == f"{BASE_URL}/copy.svg"


def test_an_svg_original_never_paints_a_canvas(builder):
    media = media_source(painting_image=image_source(mime_type="image/svg+xml"))

    assert builder.build(fragment_source(media=[media])) is None


def test_media_without_a_thumbnail_yields_none(builder):
    manifest = builder.build(
        fragment_source(media=[media_source(thumbnail_image=None)])
    )

    assert manifest.items[0].thumbnail == ()
    assert manifest.thumbnail == ()


def test_canvas_rights_mirror_the_media_rights(builder):
    assert builder.build(fragment_source()).items[0].rights == RIGHTS


def test_building_a_canvas_without_a_painting_image_is_a_programming_error(builder):
    with pytest.raises(ValueError, match="no paintable image"):
        builder._canvases.build(
            fragment_source().number, media_source(painting_image=None)
        )
