import falcon  # pyre-ignore
from falcon.media.validators.jsonschema import validate

from ebl.bibliography.application.reference_schema import ReferenceSchema
from ebl.bibliography.domain.reference import REFERENCE_DTO_SCHEMA
from ebl.fragmentarium.application.fragment_updater import FragmentUpdater
from ebl.fragmentarium.web.dtos import create_response_dto
from ebl.users.web.require_scope import require_scope

REFERENCES_DTO_SCHEMA = {
    "type": "object",
    "properties": {"references": {"type": "array", "items": REFERENCE_DTO_SCHEMA}},
    "required": ["references"],
}


class ReferencesResource:
    def __init__(self, updater: FragmentUpdater):
        self._updater = updater

    @falcon.before(require_scope, "transliterate:fragments")
    @validate(REFERENCES_DTO_SCHEMA)
    def on_post(self, req, resp, number):
        user = req.context.user
        updated_fragment, has_photo = self._updater.update_references(
            number,
            tuple(
                ReferenceSchema().load(req.media["references"], many=True)
            ),
            user,
        )
        resp.media = create_response_dto(updated_fragment, user, has_photo)
