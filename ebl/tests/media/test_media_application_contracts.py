from io import BytesIO
from typing import Sequence

import attr

from ebl.media.application import (
    MediaRepository,
    RepresentationHandle,
    MediaRepresentationStore,
    MediaService,
)
from ebl.media.domain import (
    Media,
    MediaAssociation,
    MediaChecksum,
    MediaId,
    MediaRepresentation,
    MediaRepresentations,
    MediaType,
)
from ebl.transliteration.domain.museum_number import MuseumNumber

PHOTO_ID = MediaId("550e8400-e29b-41d4-a716-446655440000")
COPY_ID = MediaId("550e8400-e29b-41d4-a716-446655440001")


class InMemoryMediaRepository(MediaRepository):
    def __init__(self, media=()):
        self._media = {item.id: item for item in media}

    def find_by_id(self, media_id):
        return self._media.get(media_id)

    def find_by_fragment(self, fragment_id):
        return tuple(
            sorted(
                (
                    item
                    for item in self._media.values()
                    if item.is_associated_with(fragment_id)
                ),
                key=lambda item: item.association_for(fragment_id).sort_order,
            )
        )

    def find_by_fragments(self, fragment_ids):
        return {
            fragment_id: self.find_by_fragment(fragment_id)
            for fragment_id in fragment_ids
        }

    def find_in_fragment(self, media_id, fragment_id):
        media = self.find_by_id(media_id)
        return media if media and media.is_associated_with(fragment_id) else None

    def find_primary_photo(self, fragment_id):
        return next(
            (
                item
                for item in self.find_by_fragment(fragment_id)
                if item.type is MediaType.PHOTO
                and item.association_for(fragment_id).is_primary
            ),
            None,
        )

    def save(self, media):
        self._media[media.id] = media
        return media.id

    def replace(self, media):
        self._media[media.id] = media
        return media.id


class InMemoryMediaService(MediaService):
    def __init__(self, repository: MediaRepository):
        self._repository = repository

    def list_fragment_media(self, fragment_id):
        return self._repository.find_by_fragment(fragment_id)

    def find_media_by_fragments(self, fragment_ids: Sequence[MuseumNumber]):
        return self._repository.find_by_fragments(fragment_ids)

    def get_fragment_media(self, fragment_id, media_id):
        return self._repository.find_in_fragment(media_id, fragment_id)


class InMemoryRepresentationStore(MediaRepresentationStore):
    def read_original(self, media):
        raise NotImplementedError

    def read_display(self, media):
        raise NotImplementedError

    def read_thumbnail(self, media, thumbnail_size):
        raise NotImplementedError

    def write_original(self, request):
        raise NotImplementedError

    def write_display(self, request):
        raise NotImplementedError

    def write_thumbnail(self, request):
        raise NotImplementedError

    def delete_representations(self, media_id):
        raise NotImplementedError


def representation() -> MediaRepresentation:
    return MediaRepresentation(
        "image/jpeg", 4000, 3000, 5242880, MediaChecksum(value="a" * 64)
    )


def media(
    media_id: MediaId,
    media_type: MediaType,
    associations,
    filename="BM-12345-obverse.jpg",
) -> Media:
    return Media(
        id=media_id,
        type=media_type,
        original_filename=filename,
        representations=MediaRepresentations(representation()),
        associations=associations,
    )


def test_repository_contract_reads_media_by_fragment_in_fragment_order() -> None:
    photo = media(
        PHOTO_ID,
        MediaType.PHOTO,
        (
            MediaAssociation(MuseumNumber.of("K.1"), 1, False),
            MediaAssociation(MuseumNumber.of("Sm.2"), 0, True),
        ),
    )
    copy = media(
        COPY_ID,
        MediaType.COPY,
        (MediaAssociation(MuseumNumber.of("K.1"), 0, True),),
    )
    repository = InMemoryMediaRepository((photo, copy))

    assert repository.find_by_fragment(MuseumNumber.of("K.1")) == (copy, photo)
    assert repository.find_by_fragment(MuseumNumber.of("Sm.2")) == (photo,)


def test_repository_contract_batch_reads_fragment_media() -> None:
    photo = media(
        PHOTO_ID,
        MediaType.PHOTO,
        (
            MediaAssociation(MuseumNumber.of("K.1"), 0, True),
            MediaAssociation(MuseumNumber.of("Sm.2"), 0, True),
        ),
    )
    repository = InMemoryMediaRepository((photo,))

    assert repository.find_by_fragments(
        (MuseumNumber.of("K.1"), MuseumNumber.of("Sm.2"))
    ) == {
        MuseumNumber.of("K.1"): (photo,),
        MuseumNumber.of("Sm.2"): (photo,),
    }


def test_repository_contract_reads_one_media_item_in_fragment_context() -> None:
    photo = media(
        PHOTO_ID,
        MediaType.PHOTO,
        (MediaAssociation(MuseumNumber.of("K.1"), 0, True),),
    )
    repository = InMemoryMediaRepository((photo,))

    assert repository.find_in_fragment(PHOTO_ID, MuseumNumber.of("K.1")) == photo
    assert repository.find_in_fragment(PHOTO_ID, MuseumNumber.of("Sm.2")) is None


def test_repository_contract_finds_primary_photo_only() -> None:
    copy = media(
        COPY_ID, MediaType.COPY, (MediaAssociation(MuseumNumber.of("K.1"), 0, True),)
    )
    photo = media(
        PHOTO_ID,
        MediaType.PHOTO,
        (MediaAssociation(MuseumNumber.of("K.1"), 1, True),),
    )
    repository = InMemoryMediaRepository((copy, photo))

    assert repository.find_primary_photo(MuseumNumber.of("K.1")) == photo


def test_repository_contract_replaces_metadata_without_changing_identity() -> None:
    photo = media(
        PHOTO_ID,
        MediaType.PHOTO,
        (MediaAssociation(MuseumNumber.of("K.1"), 0, True),),
    )
    replacement = attr.evolve(photo, caption="Replacement audit note")
    repository = InMemoryMediaRepository((photo,))

    assert repository.replace(replacement) == PHOTO_ID
    assert repository.find_by_id(PHOTO_ID) == replacement


def test_service_contract_batch_reads_fragment_media_without_building_summaries() -> (
    None
):
    photo = media(
        PHOTO_ID,
        MediaType.PHOTO,
        (
            MediaAssociation(MuseumNumber.of("K.1"), 0, True),
            MediaAssociation(MuseumNumber.of("Sm.2"), 0, True),
        ),
    )
    service = InMemoryMediaService(InMemoryMediaRepository((photo,)))

    assert service.find_media_by_fragments(
        (MuseumNumber.of("K.1"), MuseumNumber.of("Sm.2"))
    ) == {
        MuseumNumber.of("K.1"): (photo,),
        MuseumNumber.of("Sm.2"): (photo,),
    }


def test_representation_store_contract_includes_display_without_repository_expansion() -> (
    None
):
    store = InMemoryRepresentationStore()

    assert hasattr(store, "read_display")
    assert hasattr(store, "write_display")
    assert not hasattr(MediaRepository, "find_display")


def test_representation_handle_contract_includes_readable_content() -> None:
    content = BytesIO(b"media-bytes")

    handle = RepresentationHandle(
        media_id=PHOTO_ID,
        representation=representation(),
        content=content,
        content_type="image/jpeg",
        length=len(b"media-bytes"),
    )

    assert handle.content.read() == b"media-bytes"
