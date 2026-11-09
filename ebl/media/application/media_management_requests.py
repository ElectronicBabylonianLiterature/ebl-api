"""Internal commands keep transport, actor, and reservation data together."""

from dataclasses import dataclass
from typing import BinaryIO, Callable

from ebl.media.application.media_stored import StoredMedia
from ebl.media.domain import Media, MediaId
from ebl.transliteration.domain.museum_number import MuseumNumber


@dataclass(frozen=True)
class MediaUploadRequest:
    fragment_id: MuseumNumber
    actor: str
    idempotency_key: str
    metadata: dict
    content: BinaryIO
    length: int | None
    mime_type: str | None


@dataclass(frozen=True)
class MediaMutationRequest:
    fragment_id: MuseumNumber
    media_id: MediaId
    actor: str
    manager: bool
    operation: str
    metadata: dict
    authorize_associations: Callable[[Media], None]


@dataclass(frozen=True)
class MediaUploadCommit:
    request_id: str
    fingerprint: str
    lease: str
    stored: StoredMedia
    actor: str
    fragment_id: MuseumNumber


@dataclass(frozen=True)
class StoredMediaMutation:
    fragment_id: MuseumNumber
    media_id: MediaId
    actor: str
    operation: str
    change: Callable[[Media], Media]
