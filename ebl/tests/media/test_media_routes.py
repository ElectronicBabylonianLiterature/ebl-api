import falcon

from ebl.media.domain import MediaType
from ebl.tests.media.factories import (
    association,
    copy_media,
    media_reference,
    photo_media,
    representations,
)
from ebl.tests.media.route_fixtures import seed_media


def test_lists_fragment_media(
    client, media_repository, media_representation_store, public_fragment
):
    media = photo_media(
        associations=(association(fragment_id=public_fragment.number),),
        caption="Obverse",
        attribution="The British Museum",
        references=(media_reference(),),
    )
    seed_media(media_repository, media_representation_store, media)

    result = client.simulate_get(f"/fragments/{public_fragment.number}/media")

    assert result.status == falcon.HTTP_OK
    assert len(result.json["media"]) == 1
    item = result.json["media"][0]
    assert item["id"] == str(media.id)
    assert item["type"] == MediaType.PHOTO.name
    assert item["sortOrder"] == 0
    assert item["isPrimary"] is True
    assert item["caption"] == "Obverse"
    assert item["attribution"] == "The British Museum"
    assert item["references"] == [{"id": "bibliography-id"}]


def test_lists_media_representation_urls(
    client, media_repository, media_representation_store, public_fragment
):
    media = photo_media(
        associations=(association(fragment_id=public_fragment.number),),
        media_representations=representations(display_mime_type="image/jpeg"),
    )
    seed_media(media_repository, media_representation_store, media)

    result = client.simulate_get(f"/fragments/{public_fragment.number}/media")
    found = result.json["media"][0]["representations"]

    assert found["original"]["url"] == (
        f"/fragments/{public_fragment.number}/media/{media.id}/file"
    )
    assert found["display"]["url"] == (
        f"/fragments/{public_fragment.number}/media/{media.id}/display"
    )
    assert found["thumbnails"]["small"]["url"] == (
        f"/fragments/{public_fragment.number}/media/{media.id}/thumbnail/small"
    )
    assert found["original"]["mimeType"] == "image/jpeg"
    assert found["original"]["width"] == 4000
    assert found["original"]["height"] == 3000


def test_media_list_preserves_association_order_and_primary(
    client, media_repository, media_representation_store, public_fragment
):
    number = public_fragment.number
    photo = photo_media(
        associations=(association(fragment_id=number, sort_order=1, is_primary=False),)
    )
    copy = copy_media(
        associations=(association(fragment_id=number, sort_order=0, is_primary=True),)
    )
    seed_media(media_repository, media_representation_store, photo)
    seed_media(media_repository, media_representation_store, copy)

    result = client.simulate_get(f"/fragments/{number}/media")

    assert [item["id"] for item in result.json["media"]] == [
        str(copy.id),
        str(photo.id),
    ]
    assert [item["isPrimary"] for item in result.json["media"]] == [True, False]


def test_media_list_is_empty_for_a_fragment_without_media(client, public_fragment):
    result = client.simulate_get(f"/fragments/{public_fragment.number}/media")

    assert result.status == falcon.HTTP_OK
    assert result.json == {"media": []}


def test_media_list_omits_absent_optional_properties(
    client, media_repository, media_representation_store, public_fragment
):
    media = photo_media(
        associations=(association(fragment_id=public_fragment.number),),
        caption=None,
        attribution=None,
    )
    seed_media(media_repository, media_representation_store, media)

    item = client.simulate_get(f"/fragments/{public_fragment.number}/media").json[
        "media"
    ][0]

    assert "caption" not in item
    assert "attribution" not in item
    assert "references" not in item
    assert "display" not in item["representations"]


def test_media_list_never_exposes_internal_storage_handles(
    client, media_repository, media_representation_store, public_fragment
):
    media = photo_media(
        associations=(association(fragment_id=public_fragment.number),),
        media_representations=representations(display_mime_type="image/jpeg"),
    )
    stored = seed_media(media_repository, media_representation_store, media)

    body = client.simulate_get(f"/fragments/{public_fragment.number}/media").text

    for handle in stored.representations.handles:
        assert handle.value not in body
    assert "storedHandle" not in body
    assert "checksum" not in body
    assert "importSource" not in body


def test_media_list_of_another_fragment_excludes_unassociated_media(
    client,
    media_repository,
    media_representation_store,
    public_fragment,
    other_public_fragment,
):
    media = photo_media(associations=(association(fragment_id=public_fragment.number),))
    seed_media(media_repository, media_representation_store, media)

    result = client.simulate_get(f"/fragments/{other_public_fragment.number}/media")

    assert result.json == {"media": []}


def test_media_list_of_authorized_restricted_fragment_is_allowed(
    client, readable_restricted_fragment
):
    result = client.simulate_get(
        f"/fragments/{readable_restricted_fragment.number}/media"
    )

    assert result.status == falcon.HTTP_OK


def test_media_list_of_unauthorized_restricted_fragment_is_forbidden(
    client, restricted_fragment
):
    result = client.simulate_get(f"/fragments/{restricted_fragment.number}/media")

    assert result.status == falcon.HTTP_FORBIDDEN


def test_media_list_of_restricted_fragment_is_forbidden_for_guest(
    guest_client, readable_restricted_fragment
):
    result = guest_client.simulate_get(
        f"/fragments/{readable_restricted_fragment.number}/media"
    )

    assert result.status == falcon.HTTP_FORBIDDEN


def test_media_list_of_public_fragment_is_allowed_for_guest(
    guest_client, public_fragment
):
    result = guest_client.simulate_get(f"/fragments/{public_fragment.number}/media")

    assert result.status == falcon.HTTP_OK
