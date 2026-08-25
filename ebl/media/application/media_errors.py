from ebl.errors import Defect, DuplicateError, NotFoundError
from ebl.media.application.media_stored import StoredRepresentationHandle
from ebl.media.domain import MediaId, ThumbnailSize


class MediaNotFoundError(NotFoundError):
    def __init__(self, media_id: MediaId) -> None:
        super().__init__(media_id)
        self.media_id = media_id

    def __str__(self) -> str:
        return f"Media {self.media_id} not found."


class MediaAlreadyExistsError(DuplicateError):
    def __init__(self, media_id: MediaId) -> None:
        super().__init__(media_id)
        self.media_id = media_id

    def __str__(self) -> str:
        return f"Media {self.media_id} already exists."


class MediaRepresentationNotFoundError(NotFoundError):
    def __init__(self, media_id: MediaId, representation: str) -> None:
        super().__init__(media_id, representation)
        self.media_id = media_id
        self.representation = representation

    def __str__(self) -> str:
        return f"Media {self.media_id} has no {self.representation} representation."

    @classmethod
    def thumbnail(
        cls, media_id: MediaId, thumbnail_size: ThumbnailSize
    ) -> "MediaRepresentationNotFoundError":
        return cls(media_id, f"{thumbnail_size.value} thumbnail")


class StoredRepresentationMissingError(Defect):
    """Current metadata references a logical stored version that is absent.

    A server-side integrity failure, not a client error, so it is a `Defect`
    rather than a `NotFoundError`: the HTTP layer maps it to 5xx. The handle is
    kept as an attribute for logs and never appears in the message, because
    stored handles must not reach user-facing output.
    """

    def __init__(self, handle: StoredRepresentationHandle) -> None:
        super().__init__(handle)
        self.handle = handle

    def __str__(self) -> str:
        return "Stored media representation not found."
