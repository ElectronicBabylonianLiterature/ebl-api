"""Internal route for the trusted bibliography identity operation.

Kept out of `bibliography_entries.py` so that the privilege boundary is
visible: `POST /bibliography/{id_}` remains metadata-only under
`write:bibliography`, while identity changes live on a separate path behind
`admin:bibliography`. That scope matters because internal and partner routes
are served by one app behind one auth backend, so a partner M2M client holding
`write:bibliography` would otherwise reach this operation.
"""

import falcon
from falcon import Response
from falcon.media.validators.jsonschema import validate

from ebl.bibliography.application.identity_management import (
    BibliographyIdentityManagement,
)
from ebl.bibliography.domain.identity_management import (
    BIBLIOGRAPHY_IDENTITY_JSON_SCHEMA,
)
from ebl.users.web.require_scope import require_scope
from ebl.users.web.user_request import UserRequest


class BibliographyIdentityResource:
    def __init__(self, identity_management: BibliographyIdentityManagement):
        self._identity_management = identity_management

    @falcon.before(require_scope, "admin:bibliography")
    @validate(BIBLIOGRAPHY_IDENTITY_JSON_SCHEMA)
    def on_post(self, req: UserRequest, resp: Response, id_: str) -> None:
        resp.media = self._identity_management.manage_identity(
            id_, req.media, req.context.user
        )
