from enum import Enum
from typing import Optional

import attr

from ebl.media.domain import MediaId, MediaRepresentation, ThumbnailSize
from ebl.media.domain.validation import instance_of, not_blank


class StoredRepresentationRole(Enum):
    ORIGINAL = "original"
    DISPLAY = "display"
    THUMBNAIL = "thumbnail"


@attr.s(auto_attribs=True, frozen=True, str=False)
class StoredRepresentationHandle:
    media_id: MediaId = attr.ib(validator=instance_of(MediaId))
    value: str = attr.ib(validator=not_blank)
    representation: MediaRepresentation = attr.ib(
        validator=instance_of(MediaRepresentation)
    )
    role: StoredRepresentationRole = attr.ib(
        default=StoredRepresentationRole.ORIGINAL,
        kw_only=True,
        validator=instance_of(StoredRepresentationRole),
    )
    thumbnail_size: Optional[ThumbnailSize] = attr.ib(
        default=None,
        kw_only=True,
        validator=attr.validators.optional(instance_of(ThumbnailSize)),
    )

    def __attrs_post_init__(self) -> None:
        has_thumbnail_size = self.thumbnail_size is not None
        if (self.role is StoredRepresentationRole.THUMBNAIL) != has_thumbnail_size:
            raise ValueError("Only thumbnail handles have a thumbnail size.")

    def __str__(self) -> str:
        return self.value
