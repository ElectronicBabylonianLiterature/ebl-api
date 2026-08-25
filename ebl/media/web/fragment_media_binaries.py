import falcon
from falcon import Request, Response

from ebl.fragmentarium.application.fragment_finder import FragmentFinder
from ebl.fragmentarium.web.dtos import parse_museum_number
from ebl.media.application.media_errors import MediaRepresentationNotFoundError
from ebl.media.application.media_service import MediaService
from ebl.media.application.media_store import MediaRepresentationStore
from ebl.media.application.media_stored import (
    OpenRepresentation,
    StoredRepresentationHandle,
)
from ebl.media.web.media_web_base import (
    MediaResource,
    parse_media_id,
    parse_thumbnail_size,
)
from ebl.users.web.require_scope import require_fragment_read_scope

DISPLAY_REPRESENTATION = "display"


def _stream(resp: Response, opened: OpenRepresentation) -> None:
    resp.content_type = opened.representation.mime_type
    resp.content_length = opened.length
    resp.stream = opened.content


class MediaBinaryResource(MediaResource):
    def __init__(
        self,
        service: MediaService,
        finder: FragmentFinder,
        representation_store: MediaRepresentationStore,
    ) -> None:
        super().__init__(service, finder)
        self._representation_store = representation_store

    def _respond(self, resp: Response, handle: StoredRepresentationHandle) -> None:
        _stream(resp, self._representation_store.open_representation(handle))


class FragmentMediaFileResource(MediaBinaryResource):
    @falcon.before(require_fragment_read_scope)
    def on_get(self, _req: Request, resp: Response, number: str, media_id: str) -> None:
        stored_media = self._stored_media(
            parse_museum_number(number), parse_media_id(media_id)
        )
        self._respond(resp, stored_media.representations.original)


class FragmentMediaDisplayResource(MediaBinaryResource):
    @falcon.before(require_fragment_read_scope)
    def on_get(self, _req: Request, resp: Response, number: str, media_id: str) -> None:
        parsed_media_id = parse_media_id(media_id)
        stored_media = self._stored_media(parse_museum_number(number), parsed_media_id)
        handle = stored_media.representations.display
        if handle is None:
            raise MediaRepresentationNotFoundError(
                parsed_media_id, DISPLAY_REPRESENTATION
            )
        self._respond(resp, handle)


class FragmentMediaThumbnailResource(MediaBinaryResource):
    @falcon.before(require_fragment_read_scope)
    def on_get(
        self, _req: Request, resp: Response, number: str, media_id: str, size: str
    ) -> None:
        parsed_media_id = parse_media_id(media_id)
        thumbnail_size = parse_thumbnail_size(size)
        stored_media = self._stored_media(parse_museum_number(number), parsed_media_id)
        handle = stored_media.representations.thumbnail(thumbnail_size)
        if handle is None:
            raise MediaRepresentationNotFoundError.thumbnail(
                parsed_media_id, thumbnail_size
            )
        self._respond(resp, handle)
