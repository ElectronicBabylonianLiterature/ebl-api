from io import BytesIO
from typing import Dict, List, Mapping, Optional, Sequence

import attr

from ebl.media.application import (
    MediaAlreadyExistsError,
    MediaNotFoundError,
    MediaRepository,
    MediaRepresentationNotFoundError,
    MediaRepresentationStore,
    MediaService,
    RepresentationHandle,
    fragment_media_in_order,
    primary_media_for,
    primary_photo_for,
)
from ebl.media.domain import Media, MediaId, MediaRepresentation, ThumbnailSize
from ebl.transliteration.domain.museum_number import MuseumNumber

REPRESENTATION_BYTES = b"media-bytes"


class InMemoryMediaRepository(MediaRepository):
    def __init__(self, media: Sequence[Media] = ()):
        self._media: Dict[MediaId, Media] = {item.id: item for item in media}

    def find_by_id(self, media_id: MediaId) -> Optional[Media]:
        return self._media.get(media_id)

    def find_by_fragment(self, fragment_id: MuseumNumber) -> Sequence[Media]:
        return fragment_media_in_order(
            fragment_id,
            tuple(
                item
                for item in self._media.values()
                if item.is_associated_with(fragment_id)
            ),
        )

    def find_by_fragments(
        self, fragment_ids: Sequence[MuseumNumber]
    ) -> Mapping[MuseumNumber, Sequence[Media]]:
        return {
            fragment_id: self.find_by_fragment(fragment_id)
            for fragment_id in fragment_ids
        }

    def find_in_fragment(
        self, media_id: MediaId, fragment_id: MuseumNumber
    ) -> Optional[Media]:
        media = self.find_by_id(media_id)
        return media if media and media.is_associated_with(fragment_id) else None

    def find_primary_media(self, fragment_id: MuseumNumber) -> Optional[Media]:
        return primary_media_for(fragment_id, self.find_by_fragment(fragment_id))

    def find_primary_photo(self, fragment_id: MuseumNumber) -> Optional[Media]:
        return primary_photo_for(fragment_id, self.find_by_fragment(fragment_id))

    def create(self, media: Media) -> MediaId:
        if media.id in self._media:
            raise MediaAlreadyExistsError(media.id)
        self._media[media.id] = media
        return media.id

    def replace(self, media: Media) -> MediaId:
        if media.id not in self._media:
            raise MediaNotFoundError(media.id)
        self._media[media.id] = media
        return media.id

    def delete(self, media_id: MediaId) -> None:
        self._media.pop(media_id, None)


class InMemoryRepresentationStore(MediaRepresentationStore):
    def __init__(self):
        self.written_originals: List[object] = []
        self.written_displays: List[object] = []
        self.written_thumbnails: List[object] = []
        self.deleted_media_ids: List[MediaId] = []

    def read_original(self, media: Media) -> RepresentationHandle:
        return _handle(media.id, media.representations.original)

    def read_display(self, media: Media) -> RepresentationHandle:
        display = media.representations.display
        if display is None:
            raise MediaRepresentationNotFoundError(media.id, "display")
        return _handle(media.id, display)

    def read_thumbnail(
        self, media: Media, thumbnail_size: ThumbnailSize
    ) -> RepresentationHandle:
        for size, representation in media.representations.thumbnails:
            if size is thumbnail_size:
                return _handle(media.id, representation)
        raise MediaRepresentationNotFoundError.thumbnail(media.id, thumbnail_size)

    def write_original(self, request) -> None:
        self.written_originals.append(request)

    def write_display(self, request) -> None:
        self.written_displays.append(request)

    def write_thumbnail(self, request) -> None:
        self.written_thumbnails.append(request)

    def delete_representations(self, media_id: MediaId) -> None:
        self.deleted_media_ids.append(media_id)


class InMemoryMediaService(MediaService):
    def __init__(
        self,
        repository: MediaRepository,
        representation_store: Optional[MediaRepresentationStore] = None,
    ):
        self._repository = repository
        self._representation_store = (
            representation_store or InMemoryRepresentationStore()
        )

    def list_fragment_media(self, fragment_id: MuseumNumber) -> Sequence[Media]:
        return self._repository.find_by_fragment(fragment_id)

    def find_media_by_fragments(
        self, fragment_ids: Sequence[MuseumNumber]
    ) -> Mapping[MuseumNumber, Sequence[Media]]:
        return self._repository.find_by_fragments(fragment_ids)

    def get_fragment_media(
        self, fragment_id: MuseumNumber, media_id: MediaId
    ) -> Optional[Media]:
        return self._repository.find_in_fragment(media_id, fragment_id)

    def set_primary_media(
        self, fragment_id: MuseumNumber, media_id: MediaId
    ) -> Sequence[Media]:
        if self._repository.find_in_fragment(media_id, fragment_id) is None:
            raise MediaNotFoundError(media_id)

        for item in self._repository.find_by_fragment(fragment_id):
            self._repository.replace(
                _with_primary(item, fragment_id, item.id == media_id)
            )
        return self._repository.find_by_fragment(fragment_id)

    def delete_media(self, media_id: MediaId) -> None:
        if self._repository.find_by_id(media_id) is None:
            raise MediaNotFoundError(media_id)

        self._repository.delete(media_id)
        self._representation_store.delete_representations(media_id)


def _handle(
    media_id: MediaId, representation: MediaRepresentation
) -> RepresentationHandle:
    return RepresentationHandle(
        media_id=media_id,
        representation=representation,
        content=BytesIO(REPRESENTATION_BYTES),
        content_type=representation.mime_type,
        length=len(REPRESENTATION_BYTES),
    )


def _with_primary(media: Media, fragment_id: MuseumNumber, is_primary: bool) -> Media:
    return attr.evolve(
        media,
        associations=tuple(
            attr.evolve(association, is_primary=is_primary)
            if association.fragment_id == fragment_id
            else association
            for association in media.associations
        ),
    )
