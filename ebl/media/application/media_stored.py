from typing import BinaryIO, Optional, Sequence

import attr

from ebl.media.domain import Media, MediaId, MediaRepresentation, ThumbnailSize
from ebl.media.domain.validation import not_blank, positive_int, tuple_or_empty


def _thumbnail_handles_of(
    value: Optional[Sequence["StoredThumbnailRepresentation"]],
) -> tuple["StoredThumbnailRepresentation", ...]:
    return tuple_or_empty(value)


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


@attr.s(auto_attribs=True, frozen=True, str=False)
class StoredRepresentationHandle:
    """Opaque, server-internal reference to one immutable logical stored version.

    Never a route parameter, bearer capability, public DTO field, or part of a
    user-facing error message.
    """

    value: str = attr.ib(validator=not_blank)

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
        converter=_thumbnail_handles_of,
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

    def superseded_by(
        self, replacement: "StoredMediaRepresentations"
    ) -> Sequence[StoredRepresentationHandle]:
        """Handles of this state that the replacement state no longer references.

        The only handles a caller may delete after a successful replacement.
        Handles still current in `replacement` are never returned, so a
        metadata-only replacement supersedes nothing.
        """
        current = set(replacement.handles)
        return tuple(handle for handle in self.handles if handle not in current)


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

    def superseded_by(
        self, replacement: "StoredMedia"
    ) -> Sequence[StoredRepresentationHandle]:
        """Handles this media no longer references after `replacement` becomes current.

        Rejects a replacement for a different media, which would otherwise report
        every handle of this one as safe to delete.
        """
        if self.media.id != replacement.media.id:
            raise ValueError("Cannot supersede stored state of a different media.")
        return self.representations.superseded_by(replacement.representations)


@attr.s(auto_attribs=True, frozen=True)
class OpenRepresentation:
    """One opened logical stored version.

    `representation.mime_type` is the only MIME authority for responses; the
    storage provider's own content type is never trusted. The caller owns
    `content` and must close it.
    """

    media_id: MediaId
    representation: MediaRepresentation
    content: BinaryIO
    length: int = attr.ib(validator=positive_int)


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
