import falcon
from falcon.media.validators.jsonschema import validate
from ebl.require_scope import require_scope
from ebl.bibliography.reference import ReferenceType, Reference
from ebl.fragmentarium.dtos import create_response_dto


REFERENCES_DTO_SCHEMA = {
    'type': 'object',
    'properties': {
        'references': {
            'type': 'array',
            'items': {
                'type': 'object',
                'properties': {
                    'id': {
                        'type': 'string'
                    },
                    'type': {
                        'type': 'string',
                        'enum': [name for name, _
                                 in ReferenceType.__members__.items()]
                    },
                    'pages': {
                        'type': 'string'
                    },
                    'notes': {
                        'type': 'string'
                    },
                    'linesCited': {
                        'type': 'array',
                        'items': {
                            'type': 'string'
                        }
                    }
                },
                'required': [
                    'id',
                    'type',
                    'pages',
                    'notes',
                    'linesCited'
                ]
            }
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
