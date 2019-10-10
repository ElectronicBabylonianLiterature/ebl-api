import falcon
from falcon import Request, Response

from ebl.cdli.infrastructure.cdli_client import get_photo_url
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
        photo_url = get_photo_url(cdli_number)
        resp.media = {
            'photoUrl': photo_url
        }
