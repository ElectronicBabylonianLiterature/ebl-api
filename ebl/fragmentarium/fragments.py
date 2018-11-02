import falcon
from falcon.media.validators.jsonschema import validate
from ebl.require_scope import require_scope
from ebl.fragmentarium.transliterations import Transliteration


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


class FragmentsResource:
    def __init__(self, fragmentarium):
        self._fragmentarium = fragmentarium

    @falcon.before(require_scope, 'read:fragments')
    def on_get(self, req, resp, number):
        user = req.context['user']
        try:
            resp.media = (self
                          ._fragmentarium
                          .find(number)
                          .to_dict_for(user))
        except KeyError:
            resp.status = falcon.HTTP_NOT_FOUND

    @falcon.before(require_scope, 'transliterate:fragments')
    @validate(TRANSLITERATION_DTO_SCHEMA)
    def on_post(self, req, resp, number):
        def parse_request():
            try:
                return Transliteration(
                    req.media['transliteration'],
                    req.media['notes']
                )
            except (TypeError, KeyError):
                raise falcon.HTTPUnprocessableEntity()

        try:
            self._fragmentarium.update_transliteration(
                number,
                parse_request(),
                req.context['user']
            )
        except KeyError:
            resp.status = falcon.HTTP_NOT_FOUND
