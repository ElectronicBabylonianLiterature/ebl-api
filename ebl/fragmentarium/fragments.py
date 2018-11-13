import falcon
from falcon.media.validators.jsonschema import validate
from ebl.require_scope import require_scope
from ebl.fragmentarium.transliterations import Transliteration
from ebl.fragmentarium.atf import validate_atf, AtfSyntaxError


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
            raise falcon.HTTPNotFound()

    @falcon.before(require_scope, 'transliterate:fragments')
    @validate(TRANSLITERATION_DTO_SCHEMA)
    def on_post(self, req, resp, number):
        try:
            validate_atf(req.media['transliteration'])
            self._fragmentarium.update_transliteration(
                number,
                Transliteration(
                    req.media['transliteration'],
                    req.media['notes']
                ),
                req.context['user']
            )
        except AtfSyntaxError as error:
            resp.status = falcon.HTTP_UNPROCESSABLE_ENTITY
            resp.media = {
                'title': resp.status,
                'description': 'Invalid transliteration',
                'errors': [
                    {
                        'type': 'SyntaxError',
                        'description': str(error),
                        'lineNumber': error.line_number
                    }
                ]
            }
        except KeyError:
            raise falcon.HTTPNotFound()
