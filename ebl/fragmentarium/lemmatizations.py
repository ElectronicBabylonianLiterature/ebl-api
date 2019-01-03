import falcon
from falcon.media.validators.jsonschema import validate
from ebl.require_scope import require_scope
from ebl.text.lemmatization import Lemmatization


LEMMATIZATION_DTO_SCHEMA = {
    'type': 'array',
    'items': {
        'type': 'array',
        'items': {
            'type': 'object',
            'properties': {
                'value': {
                    'type': 'string'
                },
                'uniqueLemma': {
                    'type': 'array',
                    'items': {
                        'type': 'string'
                    }
                }
            },
            'required': [
                'value'
            ]
        }
    }
}


class LemmatizationResource:
    # pylint: disable=R0903
    def __init__(self, fragmentarium):
        self._fragmentarium = fragmentarium

    @falcon.before(require_scope, 'lemmatize:fragments')
    @validate(LEMMATIZATION_DTO_SCHEMA)
    def on_post(self, req, _resp, number):
        self._fragmentarium.update_lemmatization(
            number,
            Lemmatization(req.media),
            req.context['user']
        )
