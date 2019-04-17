import falcon
from falcon.media.validators.jsonschema import validate

from ebl.bibliography.reference import (REFERENCE_DTO_SCHEMA, Reference)
from ebl.fragmentarium.dtos import create_response_dto
from ebl.require_scope import require_scope

REFERENCES_DTO_SCHEMA = {
    'type': 'object',
    'properties': {
        'references': {
            'type': 'array',
            'items': REFERENCE_DTO_SCHEMA
        }
    },
    'required': ['references']
}


class ReferencesResource:
    # pylint: disable=R0903
    def __init__(self, fragmentarium):
        self._fragmentarium = fragmentarium

    @falcon.before(require_scope, 'transliterate:fragments')
    @validate(REFERENCES_DTO_SCHEMA)
    def on_post(self, req, resp, number):
        user = req.context['user']
        updated_fragment = self._fragmentarium.update_references(
            number,
            tuple(
                Reference.from_dict(reference)
                for reference in req.media['references']
            ),
            user
        )
        resp.media = create_response_dto(updated_fragment, user)
