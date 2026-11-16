import re
from typing import Optional

import falcon

from ebl.errors import DataError
from ebl.media.application.media_errors import MediaRepresentationNotFoundError
from ebl.media.application.media_storage_identity import StoredRepresentationHandle
from ebl.media.application.media_stored import StoredMedia
from ebl.media.domain import MediaId, ThumbnailSize


def _private_response(response: falcon.Response) -> None:
    response.set_header("Cache-Control", "private, no-store")
    response.set_header("Vary", "Authorization")
    response.set_header("X-Content-Type-Options", "nosniff")


def _media_id(value: str) -> MediaId:
    try:
        return MediaId(value)
    except ValueError as error:
        raise DataError("Invalid media identifier.") from error


_REVISION_TAG = re.compile(r'(?:"([0-9]{1,15})"|([0-9]{1,15}))')


def _expected_revision(req: falcon.Request) -> Optional[int]:
    """Parse `If-Match: "<revision>"` (quotes optional); None when absent."""
    header = req.get_header("If-Match")
    if header is None:
        return None
    match = _REVISION_TAG.fullmatch(header.strip())
    if match is None:
        raise DataError('If-Match must be a single media revision, e.g. "3".')
    return int(match.group(1) or match.group(2))


def _representation_handle(
    stored: StoredMedia, representation: str, size: Optional[str]
) -> StoredRepresentationHandle:
    if representation == "file":
        return stored.representations.original
    if representation == "display":
        handle = stored.representations.display
    else:
        try:
            thumbnail_size = ThumbnailSize(size)
        except ValueError as error:
            raise DataError("Invalid thumbnail size.") from error
        handle = stored.representations.thumbnail(thumbnail_size)
    if handle is None:
        raise MediaRepresentationNotFoundError(stored.media.id, representation)
    return handle
