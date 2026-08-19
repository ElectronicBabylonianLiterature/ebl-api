import re
from enum import Enum
from typing import Optional, Sequence

import attr

from ebl.media.domain.mime import normalize_mime_type
from ebl.media.domain.validation import not_blank, positive_int, tuple_or_empty

SHA256 = "sha256"


def _lower(value: str) -> str:
    return value.lower() if isinstance(value, str) else value


class ThumbnailSize(Enum):
    SMALL = "small"
    MEDIUM = "medium"
    LARGE = "large"


@attr.s(auto_attribs=True, frozen=True)
class MediaChecksum:
    algorithm: str = attr.ib(default=SHA256, converter=_lower, validator=not_blank)
    value: str = attr.ib(default="", converter=_lower, validator=not_blank)

    def __attrs_post_init__(self) -> None:
        if self.algorithm != SHA256:
            raise ValueError("Media checksum algorithm must be sha256.")
        if not re.fullmatch(r"[0-9a-f]{64}", self.value):
            raise ValueError("Media checksum value must be 64 hexadecimal characters.")


@attr.s(auto_attribs=True, frozen=True)
class MediaRepresentation:
    mime_type: str = attr.ib(converter=normalize_mime_type, validator=not_blank)
    width: int = attr.ib(validator=positive_int)
    height: int = attr.ib(validator=positive_int)
    file_size: int = attr.ib(validator=positive_int)
    checksum: Optional[MediaChecksum] = None


def _thumbnails_of(
    value: Optional[Sequence[tuple[ThumbnailSize, "MediaRepresentation"]]],
) -> tuple[tuple[ThumbnailSize, "MediaRepresentation"], ...]:
    return tuple_or_empty(value)


def _validate_thumbnails(
    _instance: object,
    _attribute: attr.Attribute,
    value: Sequence[tuple[ThumbnailSize, MediaRepresentation]],
) -> None:
    for item in value:
        if not isinstance(item, tuple) or len(item) != 2:
            raise ValueError(
                "Each thumbnail must be a (ThumbnailSize, MediaRepresentation) pair."
            )
        size, representation = item
        if not isinstance(size, ThumbnailSize):
            raise ValueError("Thumbnail size must be a ThumbnailSize member.")
        if not isinstance(representation, MediaRepresentation):
            raise ValueError("Thumbnail must contain a MediaRepresentation.")

    sizes = [size for size, _ in value]
    if len(sizes) != len(set(sizes)):
        raise ValueError("Media cannot contain duplicate thumbnail sizes.")


@attr.s(auto_attribs=True, frozen=True)
class MediaRepresentations:
    original: MediaRepresentation = attr.ib()
    thumbnails: Sequence[tuple[ThumbnailSize, MediaRepresentation]] = attr.ib(
        factory=tuple, converter=_thumbnails_of, validator=_validate_thumbnails
    )
    display: Optional[MediaRepresentation] = attr.ib(
        default=None,
        kw_only=True,
        validator=attr.validators.optional(
            attr.validators.instance_of(MediaRepresentation)
        ),
    )

    def __attrs_post_init__(self) -> None:
        if not isinstance(self.original, MediaRepresentation):
            raise ValueError("Media must contain an original representation.")
        if self.original.checksum is None:
            raise ValueError("Original representation must contain a checksum.")

    @property
    def all_representations(self) -> Sequence[MediaRepresentation]:
        representations = [self.original]
        if self.display is not None:
            representations.append(self.display)
        representations.extend(representation for _, representation in self.thumbnails)
        return tuple(representations)
