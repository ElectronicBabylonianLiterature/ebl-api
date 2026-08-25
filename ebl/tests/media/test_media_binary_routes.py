import falcon

from ebl.tests.media.factories import (
    association,
    photo_media,
    representations,
)
from ebl.tests.media.route_fixtures import (
    DISPLAY_BYTES,
    ORIGINAL_BYTES,
    THUMBNAIL_BYTES,
    seed_media,
)
from ebl.media.domain import ThumbnailSize

UNKNOWN_MEDIA_ID = "550e8400-e29b-41d4-a716-4466554400ff"


def _seed(repository, store, fragment, **kwargs):
    media = photo_media(
        associations=(association(fragment_id=fragment.number),), **kwargs
    )
    seed_media(repository, store, media)
    return media


def test_serves_the_original_file(
    client, media_repository, media_representation_store, public_fragment
):
    media = _seed(media_repository, media_representation_store, public_fragment)

    result = client.simulate_get(
        f"/fragments/{public_fragment.number}/media/{media.id}/file"
    )

    assert result.status == falcon.HTTP_OK
    assert result.headers["Content-Type"] == "image/jpeg"
    assert result.content == ORIGINAL_BYTES


def test_serves_the_display_representation(
    client, media_repository, media_representation_store, public_fragment
):
    media = _seed(
        media_repository,
        media_representation_store,
        public_fragment,
        media_representations=representations(display_mime_type="image/png"),
    )

    result = client.simulate_get(
        f"/fragments/{public_fragment.number}/media/{media.id}/display"
    )

    assert result.status == falcon.HTTP_OK
    assert result.headers["Content-Type"] == "image/png"
    assert result.content == DISPLAY_BYTES


def test_serves_a_thumbnail(
    client, media_repository, media_representation_store, public_fragment
):
    media = _seed(media_repository, media_representation_store, public_fragment)

    result = client.simulate_get(
        f"/fragments/{public_fragment.number}/media/{media.id}/thumbnail/small"
    )

    assert result.status == falcon.HTTP_OK
    assert result.content == THUMBNAIL_BYTES[ThumbnailSize.SMALL]


def test_content_length_matches_the_stored_bytes(
    client, media_repository, media_representation_store, public_fragment
):
    media = _seed(media_repository, media_representation_store, public_fragment)

    result = client.simulate_get(
        f"/fragments/{public_fragment.number}/media/{media.id}/file"
    )

    assert result.headers["Content-Length"] == str(len(ORIGINAL_BYTES))


def test_absent_display_representation_is_not_found(
    client, media_repository, media_representation_store, public_fragment
):
    media = _seed(media_repository, media_representation_store, public_fragment)

    result = client.simulate_get(
        f"/fragments/{public_fragment.number}/media/{media.id}/display"
    )

    assert result.status == falcon.HTTP_NOT_FOUND


def test_absent_thumbnail_size_is_not_found(
    client, media_repository, media_representation_store, public_fragment
):
    media = _seed(media_repository, media_representation_store, public_fragment)

    result = client.simulate_get(
        f"/fragments/{public_fragment.number}/media/{media.id}/thumbnail/large"
    )

    assert result.status == falcon.HTTP_NOT_FOUND


def test_unknown_thumbnail_size_is_rejected(
    client, media_repository, media_representation_store, public_fragment
):
    media = _seed(media_repository, media_representation_store, public_fragment)

    result = client.simulate_get(
        f"/fragments/{public_fragment.number}/media/{media.id}/thumbnail/enormous"
    )

    assert result.status == falcon.HTTP_UNPROCESSABLE_ENTITY


def test_unknown_media_is_not_found(client, public_fragment):
    result = client.simulate_get(
        f"/fragments/{public_fragment.number}/media/{UNKNOWN_MEDIA_ID}/file"
    )

    assert result.status == falcon.HTTP_NOT_FOUND


def test_invalid_media_id_is_rejected(client, public_fragment):
    result = client.simulate_get(
        f"/fragments/{public_fragment.number}/media/not-a-uuid/file"
    )

    assert result.status == falcon.HTTP_UNPROCESSABLE_ENTITY


def test_media_of_another_fragment_is_not_found(
    client,
    media_repository,
    media_representation_store,
    public_fragment,
    other_public_fragment,
):
    media = _seed(media_repository, media_representation_store, public_fragment)

    result = client.simulate_get(
        f"/fragments/{other_public_fragment.number}/media/{media.id}/file"
    )

    assert result.status == falcon.HTTP_NOT_FOUND


def test_display_of_another_fragment_is_not_found(
    client,
    media_repository,
    media_representation_store,
    public_fragment,
    other_public_fragment,
):
    media = _seed(
        media_repository,
        media_representation_store,
        public_fragment,
        media_representations=representations(display_mime_type="image/png"),
    )

    result = client.simulate_get(
        f"/fragments/{other_public_fragment.number}/media/{media.id}/display"
    )

    assert result.status == falcon.HTTP_NOT_FOUND


def test_thumbnail_of_another_fragment_is_not_found(
    client,
    media_repository,
    media_representation_store,
    public_fragment,
    other_public_fragment,
):
    media = _seed(media_repository, media_representation_store, public_fragment)

    result = client.simulate_get(
        f"/fragments/{other_public_fragment.number}/media/{media.id}/thumbnail/small"
    )

    assert result.status == falcon.HTTP_NOT_FOUND


def test_binary_of_unauthorized_restricted_fragment_is_forbidden(
    client, media_repository, media_representation_store, restricted_fragment
):
    media = _seed(media_repository, media_representation_store, restricted_fragment)

    result = client.simulate_get(
        f"/fragments/{restricted_fragment.number}/media/{media.id}/file"
    )

    assert result.status == falcon.HTTP_FORBIDDEN


def test_binary_of_authorized_restricted_fragment_is_allowed(
    client,
    media_repository,
    media_representation_store,
    readable_restricted_fragment,
):
    media = _seed(
        media_repository, media_representation_store, readable_restricted_fragment
    )

    result = client.simulate_get(
        f"/fragments/{readable_restricted_fragment.number}/media/{media.id}/file"
    )

    assert result.status == falcon.HTTP_OK
    assert result.content == ORIGINAL_BYTES


def test_authorization_is_checked_before_media_is_resolved(
    client, media_repository, media_representation_store, restricted_fragment
):
    result = client.simulate_get(
        f"/fragments/{restricted_fragment.number}/media/{UNKNOWN_MEDIA_ID}/file"
    )

    assert result.status == falcon.HTTP_FORBIDDEN


def test_binary_responses_never_expose_internal_handles(
    client, media_repository, media_representation_store, public_fragment
):
    media = photo_media(associations=(association(fragment_id=public_fragment.number),))
    stored = seed_media(media_repository, media_representation_store, media)

    result = client.simulate_get(
        f"/fragments/{public_fragment.number}/media/{media.id}/file"
    )

    for handle in stored.representations.handles:
        assert handle.value not in str(result.headers)
