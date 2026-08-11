from io import BytesIO
from typing import Dict, List, Mapping, Optional, Sequence

import attr

from ebl.media.application import (
    DisplayRepresentationWriteRequest,
    MediaAlreadyExistsError,
    MediaNotFoundError,
    MediaRepository,
    MediaRepresentationStore,
    OriginalRepresentationWriteRequest,
    RepresentationHandle,
    StoredMedia,
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
    def __init__(self, media: Sequence[StoredMedia] = ()) -> None:
        self.fail_next_replace = False
        self._media: Dict[MediaId, StoredMedia] = {
            stored_media.media.id: stored_media for stored_media in media
        }

    def find_by_id(self, media_id: MediaId) -> Optional[Media]:
        stored_media = self.find_stored_by_id(media_id)
        return stored_media.media if stored_media is not None else None

    def find_stored_by_id(self, media_id: MediaId) -> Optional[StoredMedia]:
        return self._media.get(media_id)

    def find_by_fragment(self, fragment_id: MuseumNumber) -> Sequence[Media]:
        return fragment_media_in_order(
            fragment_id,
            tuple(
                item.media
                for item in self._media.values()
                if item.media.is_associated_with(fragment_id)
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
        stored_media = self.find_stored_in_fragment(media_id, fragment_id)
        return stored_media.media if stored_media is not None else None

    def find_stored_in_fragment(
        self, media_id: MediaId, fragment_id: MuseumNumber
    ) -> Optional[StoredMedia]:
        stored_media = self.find_stored_by_id(media_id)
        if stored_media is None or not stored_media.media.is_associated_with(
            fragment_id
        ):
            return None
        return stored_media

    def find_primary_media(self, fragment_id: MuseumNumber) -> Optional[Media]:
        return primary_media_for(fragment_id, self.find_by_fragment(fragment_id))

    def find_primary_photo(self, fragment_id: MuseumNumber) -> Optional[Media]:
        return primary_photo_for(fragment_id, self.find_by_fragment(fragment_id))

    def create(self, media: StoredMedia) -> MediaId:
        if media.media.id in self._media:
            raise MediaAlreadyExistsError(media.media.id)
        self._media[media.media.id] = media
        return media.media.id

    def replace(self, media: StoredMedia) -> StoredMedia:
        if media.media.id not in self._media:
            raise MediaNotFoundError(media.media.id)
        if self.fail_next_replace:
            self.fail_next_replace = False
            raise RuntimeError("Metadata replacement failed.")
        previous = self._media[media.media.id]
        self._media[media.media.id] = media
        return previous

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


def _handle(record: StoredRepresentationRecord) -> RepresentationHandle:
    return RepresentationHandle(
        media_id=record.media_id,
        representation=record.representation,
        content=BytesIO(record.content),
        content_type=record.representation.mime_type,
        length=len(record.content),
    )
