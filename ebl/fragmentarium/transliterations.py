import falcon
from falcon.media.validators.jsonschema import validate
from ebl.require_scope import require_scope
from ebl.fragmentarium.transliteration import (
    Transliteration, TransliterationError
)
from ebl.fragmentarium.dtos import create_response_dto


TRANSLITERATION_DTO_SCHEMA = {
    'type': 'object',
    'properties': {
        'transliteration': {
            'type': 'string'
        },
        'notes': {
            'type': 'string'
        }
    },
    'required': [
        'transliteration',
        'notes'
    ]
}


class TransliterationResource:
    # pylint: disable=R0903
    def __init__(self, fragmentarium):
        self._fragmentarium = fragmentarium

    @falcon.before(require_scope, 'transliterate:fragments')
    @validate(TRANSLITERATION_DTO_SCHEMA)
    def on_post(self, req, resp, number):
        try:
            user = req.context['user']
            updated_fragment = self._fragmentarium.update_transliteration(
                number,
                Transliteration(
                    req.media['transliteration'],
                    req.media['notes']
                ),
                user
            )
            resp.media = create_response_dto(updated_fragment, user)
        except TransliterationError as error:
            resp.status = falcon.HTTP_UNPROCESSABLE_ENTITY
            resp.media = {
                'title': resp.status,
                'description': str(error),
                'errors': error.errors
            }
