import pytest

from ebl.common.domain.scopes import Scope
from ebl.iiif.application.publication import (
    IiifPublicationPolicy,
    has_paintable_representation,
    is_fragment_publicly_readable,
    is_media_publishable,
)
from ebl.tests.iiif.factories import (
    MEDIA_ID,
    OTHER_MEDIA_ID,
    fragment_source,
    image_source,
    media_source,
)

POLICY = IiifPublicationPolicy()


def test_a_fragment_without_scopes_is_publicly_readable():
    assert is_fragment_publicly_readable([])


@pytest.mark.parametrize(
    "scope", [Scope.READ_CAIC_FRAGMENTS, Scope.READ_COPENHAGEN_FRAGMENTS]
)
def test_a_scoped_fragment_is_not_publicly_readable(scope: Scope):
    assert not is_fragment_publicly_readable([scope])


def test_a_restricted_fragment_publishes_nothing():
    fragment = fragment_source(authorized_scopes=[Scope.READ_CAIC_FRAGMENTS])

    assert POLICY.publishable_media(fragment) == ()
    assert not POLICY.is_fragment_published(fragment)


def test_a_public_fragment_with_complete_media_is_published():
    fragment = fragment_source()

    assert POLICY.is_fragment_published(fragment)


def test_media_without_rights_is_not_publishable():
    assert not is_media_publishable(media_source(rights=None))


def test_non_public_media_is_not_publishable():
    assert not is_media_publishable(media_source(is_public=False))


def test_media_without_a_painting_image_is_not_publishable():
    assert not is_media_publishable(media_source(painting_image=None))


def test_svg_media_is_not_publishable():
    svg = media_source(painting_image=image_source(mime_type="image/svg+xml"))

    assert not has_paintable_representation(svg)
    assert not is_media_publishable(svg)


@pytest.mark.parametrize("dimensions", [{"canvas_width": 0}, {"canvas_height": 0}])
def test_media_without_canvas_dimensions_is_not_publishable(dimensions: dict):
    assert not is_media_publishable(media_source(**dimensions))


def test_publishable_media_is_ordered_by_sort_order():
    first = media_source(OTHER_MEDIA_ID, sort_order=1)
    second = media_source(MEDIA_ID, sort_order=0)
    fragment = fragment_source(media=[first, second])

    assert [item.media_id for item in POLICY.publishable_media(fragment)] == [
        MEDIA_ID,
        OTHER_MEDIA_ID,
    ]


def test_equal_sort_orders_are_broken_by_media_identity():
    first = media_source(OTHER_MEDIA_ID, sort_order=0)
    second = media_source(MEDIA_ID, sort_order=0)
    fragment = fragment_source(media=[first, second])

    assert [item.media_id for item in POLICY.publishable_media(fragment)] == [
        MEDIA_ID,
        OTHER_MEDIA_ID,
    ]


def test_unpublishable_media_is_excluded():
    fragment = fragment_source(
        media=[media_source(MEDIA_ID), media_source(OTHER_MEDIA_ID, rights=None)]
    )

    assert [item.media_id for item in POLICY.publishable_media(fragment)] == [MEDIA_ID]


def test_uniform_terms_are_required():
    media = [
        media_source(MEDIA_ID),
        media_source(
            OTHER_MEDIA_ID, rights="http://creativecommons.org/licenses/by/4.0/"
        ),
    ]

    assert not POLICY.has_uniform_terms(media)
    assert not POLICY.is_fragment_published(fragment_source(media=media))


def test_differing_attributions_are_not_uniform():
    media = [media_source(MEDIA_ID), media_source(OTHER_MEDIA_ID, attribution="Other")]

    assert not POLICY.has_uniform_terms(media)


def test_common_terms_are_returned_when_uniform():
    media = POLICY.publishable_media(fragment_source())

    assert POLICY.common_rights(media) == media[0].rights
    assert POLICY.common_attribution(media) == media[0].attribution


def test_common_terms_are_none_when_they_disagree():
    media = [media_source(MEDIA_ID), media_source(OTHER_MEDIA_ID, attribution="Other")]

    assert POLICY.common_attribution(media) is None


def test_a_fragment_without_media_is_not_published():
    assert not POLICY.is_fragment_published(fragment_source(media=[]))
