from ebl.errors import DuplicateError, NotFoundError
from ebl.media.domain import MediaId, ThumbnailSize


class MediaNotFoundError(NotFoundError):
    def __init__(self, media_id: MediaId):
        super().__init__(media_id)
        self.media_id = media_id

    def __str__(self) -> str:
        return f"Media {self.media_id} not found."


class MediaAlreadyExistsError(DuplicateError):
    def __init__(self, media_id: MediaId):
        super().__init__(media_id)
        self.media_id = media_id

    def __str__(self) -> str:
        return f"Media {self.media_id} already exists."


class MediaRepresentationNotFoundError(NotFoundError):
    def __init__(self, media_id: MediaId, representation: str):
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
