from abc import ABC, abstractmethod
from enum import Enum
from typing import BinaryIO, Mapping, Optional, Sequence

import attr

from ebl.media.domain import (
    Media,
    MediaId,
    MediaRepresentation,
    ThumbnailSize,
)
from ebl.transliteration.domain.museum_number import MuseumNumber


class ImportMode(Enum):
    DRY_RUN = "dry-run"
    SKIP_EXISTING = "skip-existing"
    REPLACE = "replace"


@attr.s(auto_attribs=True, frozen=True)
class RepresentationHandle:
    media_id: MediaId
    representation: MediaRepresentation
    content: BinaryIO
    content_type: str
    length: int


@attr.s(auto_attribs=True, frozen=True)
class RepresentationWriteRequest:
    media_id: MediaId
    content: BinaryIO
    representation: MediaRepresentation
    thumbnail_size: Optional[ThumbnailSize] = None


@attr.s(auto_attribs=True, frozen=True)
class ImportRequest:
    mode: ImportMode
    source_name: str
    fragment_ids: Sequence[MuseumNumber] = ()


@attr.s(auto_attribs=True, frozen=True)
class ImportReport:
    created: int = 0
    skipped: int = 0
    replaced: int = 0
    errors: Sequence[str] = ()
    warnings: Sequence[str] = ()


@attr.s(auto_attribs=True, frozen=True)
class BackfillRequest:
    dry_run: bool = True
    batch_size: Optional[int] = None
    resume_after: Optional[str] = None


@attr.s(auto_attribs=True, frozen=True)
class BackfillReport:
    scanned: int = 0
    candidates: int = 0
    reports: Mapping[str, Sequence[str]] = attr.Factory(dict)


class MediaReader(ABC):
    @abstractmethod
    def find_by_id(self, media_id: MediaId) -> Optional[Media]:
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
    def find_primary_photo(self, fragment_id: MuseumNumber) -> Optional[Media]:
        raise NotImplementedError


class MediaWriter(ABC):
    @abstractmethod
    def save(self, media: Media) -> MediaId:
        raise NotImplementedError

    @abstractmethod
    def replace(self, media: Media) -> MediaId:
        raise NotImplementedError


class MediaRepository(MediaReader, MediaWriter, ABC):
    """Persistence-agnostic contract for future media metadata storage."""


class MediaRepresentationStore(ABC):
    @abstractmethod
    def read_original(self, media: Media) -> RepresentationHandle:
        raise NotImplementedError

    @abstractmethod
    def read_display(self, media: Media) -> RepresentationHandle:
        raise NotImplementedError

    @abstractmethod
    def read_thumbnail(
        self, media: Media, thumbnail_size: ThumbnailSize
    ) -> RepresentationHandle:
        raise NotImplementedError

    @abstractmethod
    def write_original(self, request: RepresentationWriteRequest) -> None:
        raise NotImplementedError

    @abstractmethod
    def write_display(self, request: RepresentationWriteRequest) -> None:
        raise NotImplementedError

    @abstractmethod
    def write_thumbnail(self, request: RepresentationWriteRequest) -> None:
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


class MediaImporter(ABC):
    @abstractmethod
    def import_media(self, request: ImportRequest) -> ImportReport:
        raise NotImplementedError


class MediaBackfill(ABC):
    @abstractmethod
    def backfill(self, request: BackfillRequest) -> BackfillReport:
        raise NotImplementedError
