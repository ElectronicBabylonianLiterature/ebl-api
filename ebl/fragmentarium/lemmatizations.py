import falcon
from falcon.media.validators.jsonschema import validate
from ebl.require_scope import require_scope
from ebl.text.lemmatization import Lemmatization
from ebl.fragmentarium.dtos import create_response_dto


LEMMATIZATION_DTO_SCHEMA = {
    'type': 'object',
    'properties': {
        'lemmatization': {
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
    },
    'required': ['lemmatization']
}


class LemmatizationResource:
    # pylint: disable=R0903
    def __init__(self, fragmentarium):
        self._fragmentarium = fragmentarium

    @falcon.before(require_scope, 'lemmatize:fragments')
    @validate(LEMMATIZATION_DTO_SCHEMA)
    def on_post(self, req, resp, number):
        user = req.context['user']
        updated_fragment = self._fragmentarium.update_lemmatization(
            number,
            Lemmatization.from_list(req.media['lemmatization']),
            user
        )
        resp.media = create_response_dto(updated_fragment, user)
