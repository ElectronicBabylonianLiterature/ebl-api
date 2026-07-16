from typing import Sequence, cast

import falcon
from marshmallow import Schema, fields, post_load

from ebl.bibliography.application.reference_schema import ReferenceSchema
from ebl.bibliography.domain.reference import Reference
from ebl.fragmentarium.application.fragment_updater import FragmentUpdater
from ebl.fragmentarium.web.dtos import FragmentDtoFactory, parse_museum_number
from ebl.marshmallowschema import validate
from ebl.users.domain.user import User
from ebl.users.web.require_scope import require_scope


class ReferencesDtoSchema(Schema):
    references = fields.Nested(ReferenceSchema, required=True, many=True)

    @post_load
    def get_references(self, data, **kwargs) -> Sequence[Reference]:
        return tuple(data["references"])


class ReferencesResource:
    def __init__(
        self, updater: FragmentUpdater, dto_factory: FragmentDtoFactory
    ) -> None:
        self._updater = updater
        self._dto_factory = dto_factory

    @falcon.before(require_scope, "transliterate:fragments")
    @validate(ReferencesDtoSchema())
    def on_post(self, req, resp, number) -> None:
        user: User = req.context["user"]
        updated_fragment, has_photo = self._updater.update_references(
            parse_museum_number(number),
            cast(Sequence[Reference], ReferencesDtoSchema().load(req.media)),
            user,
        )
        resp.media = self._dto_factory.create(updated_fragment, user, has_photo)
