import falcon
from falcon import Request, Response

from ebl.fragmentarium.web.dtos import parse_museum_number
from ebl.media.application.media_dtos import FragmentMediaResponseDto
from ebl.media.application.media_schemas import FragmentMediaResponseDtoSchema
from ebl.media.web.media_web_base import MediaResource
from ebl.users.web.require_scope import require_fragment_read_scope


class FragmentMediaResource(MediaResource):
    @falcon.before(require_fragment_read_scope)
    def on_get(self, _req: Request, resp: Response, number: str) -> None:
        fragment_id = parse_museum_number(number)
        media = self._service.list_fragment_media(fragment_id)
        resp.media = FragmentMediaResponseDtoSchema().dump(
            FragmentMediaResponseDto.of(fragment_id, media)
        )
