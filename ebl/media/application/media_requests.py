from enum import Enum
from typing import BinaryIO, Mapping, Optional, Sequence

import attr

from ebl.media.domain import Media, MediaId, MediaRepresentation, ThumbnailSize
from ebl.transliteration.domain.museum_number import MuseumNumber


def _not_blank(_instance: object, attribute: attr.Attribute, value: str) -> None:
    if not value.strip():
        raise ValueError(f"Attribute {attribute.name} cannot be blank.")


def _tuple_of(
    value: Optional[Sequence["StoredThumbnailRepresentation"]],
) -> tuple["StoredThumbnailRepresentation", ...]:
    return tuple(value or ())


def _validate_thumbnail_handles(
    _instance: object,
    _attribute: attr.Attribute,
    value: Sequence["StoredThumbnailRepresentation"],
) -> None:
    sizes = [thumbnail.size for thumbnail in value]
    if len(sizes) != len(set(sizes)):
        raise ValueError("Stored media cannot contain duplicate thumbnail sizes.")


def _validate_unique_handles(value: Sequence["StoredRepresentationHandle"]) -> None:
    if len(value) != len(set(value)):
        raise ValueError(
            "Stored media cannot contain duplicate representation handles."
        )


class ImportMode(Enum):
    DRY_RUN = "dry-run"
    SKIP_EXISTING = "skip-existing"
    REPLACE = "replace"


@attr.s(auto_attribs=True, frozen=True, str=False)
class StoredRepresentationHandle:
    value: str = attr.ib(validator=_not_blank)

    def __str__(self) -> str:
        return self.value


@attr.s(auto_attribs=True, frozen=True)
class StoredThumbnailRepresentation:
    size: ThumbnailSize = attr.ib(validator=attr.validators.instance_of(ThumbnailSize))
    handle: StoredRepresentationHandle = attr.ib(
        validator=attr.validators.instance_of(StoredRepresentationHandle)
    )


@attr.s(auto_attribs=True, frozen=True)
class StoredMediaRepresentations:
    original: StoredRepresentationHandle = attr.ib(
        validator=attr.validators.instance_of(StoredRepresentationHandle)
    )
    thumbnails: tuple[StoredThumbnailRepresentation, ...] = attr.ib(
        factory=tuple,
        converter=_tuple_of,
        validator=[
            attr.validators.deep_iterable(
                member_validator=attr.validators.instance_of(
                    StoredThumbnailRepresentation
                )
            ),
            _validate_thumbnail_handles,
        ],
    )
    display: Optional[StoredRepresentationHandle] = attr.ib(
        default=None,
        kw_only=True,
        validator=attr.validators.optional(
            attr.validators.instance_of(StoredRepresentationHandle)
        ),
    )

    @property
    def handles(self) -> Sequence[StoredRepresentationHandle]:
        handles = [self.original]
        if self.display is not None:
            handles.append(self.display)
        handles.extend(thumbnail.handle for thumbnail in self.thumbnails)
        return tuple(handles)

    def __attrs_post_init__(self) -> None:
        _validate_unique_handles(self.handles)

    def thumbnail(self, size: ThumbnailSize) -> Optional[StoredRepresentationHandle]:
        return next(
            (
                thumbnail.handle
                for thumbnail in self.thumbnails
                if thumbnail.size is size
            ),
            None,
        )


@attr.s(auto_attribs=True, frozen=True)
class StoredMedia:
    media: Media = attr.ib(validator=attr.validators.instance_of(Media))
    representations: StoredMediaRepresentations = attr.ib(
        validator=attr.validators.instance_of(StoredMediaRepresentations)
    )

    def __attrs_post_init__(self) -> None:
        display_mismatch = (
            self.media.representations.display is None
            and self.representations.display is not None
        ) or (
            self.media.representations.display is not None
            and self.representations.display is None
        )
        media_thumbnail_sizes = {
            size for size, _ in self.media.representations.thumbnails
        }
        stored_thumbnail_sizes = {
            thumbnail.size for thumbnail in self.representations.thumbnails
        }
        if display_mismatch or media_thumbnail_sizes != stored_thumbnail_sizes:
            raise ValueError("Stored media representations must match media metadata.")


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
