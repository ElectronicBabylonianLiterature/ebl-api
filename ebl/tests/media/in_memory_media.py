from io import BytesIO
from typing import Dict, List, Mapping, Optional, Sequence

import attr

from ebl.media.application import (
    DisplayRepresentationWriteRequest,
    MediaAlreadyExistsError,
    MediaNotFoundError,
    MediaRepository,
    MediaRepresentationStore,
    OpenRepresentation,
    OriginalRepresentationWriteRequest,
    StoredMedia,
    StoredRepresentationHandle,
    StoredRepresentationMissingError,
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
    def __init__(
        self,
        media: Sequence[StoredMedia] = (),
        call_log: Optional[List[str]] = None,
    ) -> None:
        self.fail_next_replace = False
        self.call_log = call_log if call_log is not None else []
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
        return self.replace_many((media,))[0]

    def replace_many(self, media: Sequence[StoredMedia]) -> Sequence[StoredMedia]:
        media_ids = [item.media.id for item in media]
        if len(media_ids) != len(set(media_ids)):
            raise ValueError("Cannot replace the same media twice in one batch.")
        for media_id in media_ids:
            if media_id not in self._media:
                raise MediaNotFoundError(media_id)
        if self.fail_next_replace:
            self.fail_next_replace = False
            raise RuntimeError("Metadata replacement failed.")

        previous = tuple(self._media[media_id] for media_id in media_ids)
        for item in media:
            self._media[item.media.id] = item
        return previous

    def delete(self, media_id: MediaId) -> None:
        self.call_log.append("repository.delete")
        self._media.pop(media_id, None)


class InMemoryRepresentationStore(MediaRepresentationStore):
    def __init__(self, call_log: Optional[List[str]] = None) -> None:
        self.written_originals: List[object] = []
        self.written_displays: List[object] = []
        self.written_thumbnails: List[object] = []
        self.deleted_handles: List[StoredRepresentationHandle] = []
        self.deleted_media_ids: List[MediaId] = []
        self.delete_failures: List[StoredRepresentationHandle] = []
        self.call_log = call_log if call_log is not None else []
        self._records: Dict[StoredRepresentationHandle, StoredRepresentationRecord] = {}
        self._next_handle = 0

    def open_representation(
        self, handle: StoredRepresentationHandle
    ) -> OpenRepresentation:
        try:
            record = self._records[handle]
        except KeyError as error:
            raise StoredRepresentationMissingError(handle) from error
        return _open_representation(record)

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
        self.call_log.append("store.delete_representations")
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


def _open_representation(record: StoredRepresentationRecord) -> OpenRepresentation:
    return OpenRepresentation(
        media_id=record.media_id,
        representation=record.representation,
        content=BytesIO(record.content),
        length=len(record.content),
    )
