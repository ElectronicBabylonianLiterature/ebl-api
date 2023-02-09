from falcon import Request, Response
from ebl.cdli.infrastructure.cdli_client import (
    get_detail_line_art_url,
    get_line_art_url,
    get_photo_url,
)


class CdliResource:
    def on_get(self, req: Request, resp: Response, cdli_number: str):
        resp.media = {
            "photoUrl": get_photo_url(cdli_number),
            "lineArtUrl": get_line_art_url(cdli_number),
            "detailLineArtUrl": get_detail_line_art_url(cdli_number),
        }
