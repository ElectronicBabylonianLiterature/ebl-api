from abc import ABC, abstractmethod
from typing import Mapping, Optional, Sequence

from ebl.media.application.media_requests import (
    BackfillReport,
    BackfillRequest,
    DisplayRepresentationWriteRequest,
    ImportReport,
    ImportRequest,
    OriginalRepresentationWriteRequest,
    RepresentationHandle,
    StoredMedia,
    StoredRepresentationHandle,
    ThumbnailRepresentationWriteRequest,
)
from ebl.media.domain import Media, MediaId
from ebl.transliteration.domain.museum_number import MuseumNumber


class MediaReader(ABC):
    @abstractmethod
    def find_by_id(self, media_id: MediaId) -> Optional[Media]:
        raise NotImplementedError

    @abstractmethod
    def find_stored_by_id(self, media_id: MediaId) -> Optional[StoredMedia]:
        raise NotImplementedError

    @abstractmethod
    def find_by_fragment(self, fragment_id: MuseumNumber) -> Sequence[Media]:
        raise NotImplementedError

    @abstractmethod
    def find_by_fragments(
        self, fragment_ids: Sequence[MuseumNumber]
    ) -> Mapping[MuseumNumber, Sequence[Media]]:
        raise NotImplementedError

    @abstractmethod
    def find_in_fragment(
        self, media_id: MediaId, fragment_id: MuseumNumber
    ) -> Optional[Media]:
        raise NotImplementedError

    @abstractmethod
    def find_stored_in_fragment(
        self, media_id: MediaId, fragment_id: MuseumNumber
    ) -> Optional[StoredMedia]:
        raise NotImplementedError

    @abstractmethod
    def find_primary_media(self, fragment_id: MuseumNumber) -> Optional[Media]:
        raise NotImplementedError

    @abstractmethod
    def find_primary_photo(self, fragment_id: MuseumNumber) -> Optional[Media]:
        raise NotImplementedError


class MediaWriter(ABC):
    @abstractmethod
    def create(self, media: StoredMedia) -> MediaId:
        raise NotImplementedError

    @abstractmethod
    def replace(self, media: StoredMedia) -> StoredMedia:
        raise NotImplementedError

    @abstractmethod
    def delete(self, media_id: MediaId) -> None:
        raise NotImplementedError


class MediaRepository(MediaReader, MediaWriter, ABC):
    pass


class MediaRepresentationStore(ABC):
    @abstractmethod
    def open_representation(
        self, handle: StoredRepresentationHandle
    ) -> RepresentationHandle:
        raise NotImplementedError

    @abstractmethod
    def write_original(
        self, request: OriginalRepresentationWriteRequest
    ) -> StoredRepresentationHandle:
        raise NotImplementedError

    @abstractmethod
    def write_display(
        self, request: DisplayRepresentationWriteRequest
    ) -> StoredRepresentationHandle:
        raise NotImplementedError

    @abstractmethod
    def write_thumbnail(
        self, request: ThumbnailRepresentationWriteRequest
    ) -> StoredRepresentationHandle:
        raise NotImplementedError

    @abstractmethod
    def delete_representation(self, handle: StoredRepresentationHandle) -> None:
        raise NotImplementedError

    @abstractmethod
    def delete_representations(self, media_id: MediaId) -> None:
        raise NotImplementedError


class MediaService(ABC):
    @abstractmethod
    def list_fragment_media(self, fragment_id: MuseumNumber) -> Sequence[Media]:
        raise NotImplementedError

    @abstractmethod
    def find_media_by_fragments(
        self, fragment_ids: Sequence[MuseumNumber]
    ) -> Mapping[MuseumNumber, Sequence[Media]]:
        raise NotImplementedError

    @abstractmethod
    def get_fragment_media(
        self, fragment_id: MuseumNumber, media_id: MediaId
    ) -> Optional[Media]:
        raise NotImplementedError

    @abstractmethod
    def get_stored_fragment_media(
        self, fragment_id: MuseumNumber, media_id: MediaId
    ) -> Optional[StoredMedia]:
        raise NotImplementedError

    @abstractmethod
    def set_primary_media(
        self, fragment_id: MuseumNumber, media_id: MediaId
    ) -> Sequence[Media]:
        raise NotImplementedError

    @abstractmethod
    def delete_media(self, media_id: MediaId) -> None:
        raise NotImplementedError


class MediaImporter(ABC):
    @abstractmethod
    def import_media(self, request: ImportRequest) -> ImportReport:
        raise NotImplementedError


class MediaBackfill(ABC):
    @abstractmethod
    def backfill(self, request: BackfillRequest) -> BackfillReport:
        raise NotImplementedError
