from typing import Sequence

import falcon  # pyre-ignore
from marshmallow import Schema, fields, post_load  # pyre-ignore[21]

from ebl.bibliography.application.reference_schema import ReferenceSchema
from ebl.bibliography.domain.reference import Reference
from ebl.fragmentarium.application.fragment_updater import FragmentUpdater
from ebl.fragmentarium.web.dtos import create_response_dto
from ebl.marshmallowschema import validate
from ebl.users.web.require_scope import require_scope


class ReferencesDtoSchema(Schema):  # pyre-ignore[11]
    references = fields.Nested(ReferenceSchema, required=True, many=True)

    @post_load
    def get_references(self, data, **kwargs) -> Sequence[Reference]:
        return tuple(data["references"])


class ReferencesResource:
    def __init__(self, updater: FragmentUpdater) -> None:
        self._updater = updater

    @falcon.before(require_scope, "transliterate:fragments")
    @validate(ReferencesDtoSchema())
    def on_post(self, req, resp, number) -> None:
        user = req.context.user
        updated_fragment, has_photo = self._updater.update_references(
            number,
            ReferencesDtoSchema().load(req.media),  # pyre-ignore[16]
            user,
        )
        resp.media = create_response_dto(updated_fragment, user, has_photo)
