from typing import Optional, cast

import falcon

from ebl.errors import DataError, Defect
from ebl.fragmentarium.application.fragment_repository import FragmentRepository
from ebl.fragmentarium.web.dtos import parse_museum_number
from ebl.media.application.media_dtos import FragmentMediaResponseDto
from ebl.media.application.media_errors import (
    MediaNotFoundError,
    MediaRepresentationNotFoundError,
)
from ebl.media.application.media_runtime import MediaRuntime
from ebl.media.application.media_schemas import FragmentMediaResponseDtoSchema
from ebl.media.application.media_storage_identity import StoredRepresentationHandle
from ebl.media.application.media_stored import StoredMedia
from ebl.media.domain import MediaId, ThumbnailSize
from ebl.media.domain.mime import is_svg_mime_type
from ebl.transliteration.domain.museum_number import MuseumNumber
from ebl.users.domain.user import User


def _private_response(response: falcon.Response) -> None:
    response.set_header("Cache-Control", "private, no-store")
    response.set_header("Vary", "Authorization")
    response.set_header("X-Content-Type-Options", "nosniff")


def _media_id(value: str) -> MediaId:
    try:
        return MediaId(value)
    except ValueError as error:
        raise DataError("Invalid media identifier.") from error


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


class MediaResource:
    def __init__(self, fragments: FragmentRepository, runtime: MediaRuntime) -> None:
        self._fragments = fragments
        self._runtime = runtime

    def _authorized_fragment(self, request: falcon.Request) -> MuseumNumber:
        value = request.get_param("fragment", required=True)
        if not isinstance(value, str) or not isinstance(
            request.params["fragment"], str
        ):
            raise DataError("A single fragment identifier is required.")
        number = parse_museum_number(value)
        scopes = self._fragments.query_read_scopes(number)
        user = cast(User, request.context["user"])
        if not user.can_read_fragment(scopes):
            raise falcon.HTTPForbidden()
        return number

    def on_get(self, req: falcon.Request, resp: falcon.Response) -> None:
        _private_response(resp)
        number = self._authorized_fragment(req)
        media = self._runtime.service.list_fragment_media(number)
        resp.media = FragmentMediaResponseDtoSchema().dump(
            FragmentMediaResponseDto.of(number, media)
        )

    def on_get_binary(
        self,
        req: falcon.Request,
        resp: falcon.Response,
        media_id: str,
        representation: str,
        size: Optional[str] = None,
    ) -> None:
        _private_response(resp)
        number = self._authorized_fragment(req)
        identifier = _media_id(media_id)
        stored = self._runtime.service.get_stored_fragment_media(number, identifier)
        if stored is None:
            raise MediaNotFoundError(identifier)
        if representation not in {"file", "display", "thumbnail"}:
            raise falcon.HTTPNotFound()
        handle = _representation_handle(stored, representation, size)
        opened = self._runtime.store.open_representation(handle)
        if (
            opened.media_id != identifier
            or opened.representation != handle.representation
        ):
            opened.content.close()
            raise Defect("Invalid stored media representation.")
        resp.content_type = opened.representation.mime_type
        resp.content_length = opened.length
        if is_svg_mime_type(opened.representation.mime_type):
            resp.downloadable_as = f"{identifier}.svg"
            resp.set_header("Content-Security-Policy", "sandbox; default-src 'none'")
        resp.stream = opened.content

    def on_get_thumbnail(
        self,
        req: falcon.Request,
        resp: falcon.Response,
        media_id: str,
        size: str,
    ) -> None:
        self.on_get_binary(req, resp, media_id, "thumbnail", size)
