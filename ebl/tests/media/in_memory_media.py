from io import BytesIO
from typing import Dict, List, Mapping, Optional, Sequence

import attr

from ebl.media.application import (
    DisplayRepresentationWriteRequest,
    MediaAlreadyExistsError,
    MediaNotFoundError,
    MediaRepository,
    MediaRepresentationStore,
    MediaService,
    OriginalRepresentationWriteRequest,
    RepresentationHandle,
    StoredRepresentationHandle,
    StoredRepresentationNotFoundError,
    ThumbnailRepresentationWriteRequest,
    fragment_media_in_order,
    primary_media_for,
    primary_photo_for,
)
from ebl.media.domain import Media, MediaId, MediaRepresentation
from ebl.transliteration.domain.museum_number import MuseumNumber

REPRESENTATION_BYTES = b"media-bytes"


@attr.s(auto_attribs=True, frozen=True)
class StoredRepresentationRecord:
    media_id: MediaId
    representation: MediaRepresentation
    content: bytes


class InMemoryMediaRepository(MediaRepository):
    def __init__(self, media: Sequence[Media] = ()) -> None:
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
    def __init__(self) -> None:
        self.written_originals: List[object] = []
        self.written_displays: List[object] = []
        self.written_thumbnails: List[object] = []
        self.deleted_handles: List[StoredRepresentationHandle] = []
        self.deleted_media_ids: List[MediaId] = []
        self.delete_failures: List[StoredRepresentationHandle] = []
        self._records: Dict[StoredRepresentationHandle, StoredRepresentationRecord] = {}
        self._next_handle = 0

    def open_representation(
        self, handle: StoredRepresentationHandle
    ) -> RepresentationHandle:
        try:
            record = self._records[handle]
        except KeyError as error:
            raise StoredRepresentationNotFoundError(handle) from error
        return _handle(record)

    def write_original(
        self, request: OriginalRepresentationWriteRequest
    ) -> StoredRepresentationHandle:
        self.written_originals.append(request)
        return self._write(request)

    def write_display(
        self, request: DisplayRepresentationWriteRequest
    ) -> StoredRepresentationHandle:
        self.written_displays.append(request)
        return self._write(request)

    def write_thumbnail(
        self, request: ThumbnailRepresentationWriteRequest
    ) -> StoredRepresentationHandle:
        self.written_thumbnails.append(request)
        return self._write(request)

    def delete_representation(self, handle: StoredRepresentationHandle) -> None:
        if handle in self.delete_failures:
            raise RuntimeError("Stored representation delete failed.")
        self.deleted_handles.append(handle)
        self._records.pop(handle, None)

    def delete_representations(self, media_id: MediaId) -> None:
        self.deleted_media_ids.append(media_id)
        for handle, record in tuple(self._records.items()):
            if record.media_id == media_id:
                self.delete_representation(handle)

    def fail_deleting(self, handle: StoredRepresentationHandle) -> None:
        self.delete_failures.append(handle)

    def contains(self, handle: StoredRepresentationHandle) -> bool:
        return handle in self._records

    def _write(
        self,
        request: OriginalRepresentationWriteRequest
        | DisplayRepresentationWriteRequest
        | ThumbnailRepresentationWriteRequest,
    ) -> StoredRepresentationHandle:
        self._next_handle += 1
        handle = StoredRepresentationHandle(
            f"stored-representation-{self._next_handle}"
        )
        self._records[handle] = StoredRepresentationRecord(
            request.media_id, request.representation, request.content.read()
        )
        return handle


class InMemoryMediaService(MediaService):
    def __init__(
        self,
        repository: MediaRepository,
        representation_store: Optional[MediaRepresentationStore] = None,
    ) -> None:
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


def _handle(record: StoredRepresentationRecord) -> RepresentationHandle:
    return RepresentationHandle(
        media_id=record.media_id,
        representation=record.representation,
        content=BytesIO(record.content),
        content_type=record.representation.mime_type,
        length=len(record.content),
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
