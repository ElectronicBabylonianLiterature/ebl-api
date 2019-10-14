import falcon
from falcon import Request, Response

from ebl.cdli.infrastructure.cdli_client import get_photo_url, \
    get_line_art_url, get_detail_line_art_url
from ebl.users.web.require_scope import require_scope


class CdliResource:

    @falcon.before(require_scope, 'read:fragments')
    def on_get(self, req: Request, resp: Response, cdli_number: str):
        """---
        description: Gets URLs for the given CDLI number
        responses:
          200:
            description: CDLI info
            content:
              application/json:
                schema:
                  properties:
                    photoUrl:
                      type: string
                      nullable: true
                    lineArtUrl:
                      type: string
                      nullable: true
                    detailLineArtUrl:
                      type: string
                      nullable: true
                  required:
                  - photoUrl
                  type: object
        security:
        - auth0:
          - read:fragments
        parameters:
        - in: path
          name: cdli_number
          schema:
            type: string
        """
        resp.media = {
            'photoUrl': get_photo_url(cdli_number),
            'lineArtUrl': get_line_art_url(cdli_number),
            'detailLineArtUrl': get_detail_line_art_url(cdli_number)
        }
