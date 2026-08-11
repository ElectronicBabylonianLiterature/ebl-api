from enum import Enum
from typing import BinaryIO, Mapping, Optional, Sequence

import attr

from ebl.media.domain import MediaId, MediaRepresentation, ThumbnailSize
from ebl.transliteration.domain.museum_number import MuseumNumber


def _not_empty(_, attribute: attr.Attribute, value: str) -> None:
    if not value:
        raise ValueError(f"Attribute {attribute.name} cannot be empty.")


class ImportMode(Enum):
    DRY_RUN = "dry-run"
    SKIP_EXISTING = "skip-existing"
    REPLACE = "replace"


@attr.s(auto_attribs=True, frozen=True, str=False)
class StoredRepresentationHandle:
    value: str = attr.ib(validator=_not_empty)

    def __str__(self) -> str:
        return self.value


@attr.s(auto_attribs=True, frozen=True)
class RepresentationHandle:
    media_id: MediaId
    representation: MediaRepresentation
    content: BinaryIO
    content_type: str
    length: int


@attr.s(auto_attribs=True, frozen=True)
class _RepresentationWriteRequest:
    media_id: MediaId
    content: BinaryIO
    representation: MediaRepresentation


@attr.s(auto_attribs=True, frozen=True)
class OriginalRepresentationWriteRequest(_RepresentationWriteRequest):
    pass


@attr.s(auto_attribs=True, frozen=True)
class DisplayRepresentationWriteRequest(_RepresentationWriteRequest):
    pass


@attr.s(auto_attribs=True, frozen=True)
class ThumbnailRepresentationWriteRequest(_RepresentationWriteRequest):
    thumbnail_size: ThumbnailSize = attr.ib(
        validator=attr.validators.instance_of(ThumbnailSize)
    )


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
    failed: int = 0
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
