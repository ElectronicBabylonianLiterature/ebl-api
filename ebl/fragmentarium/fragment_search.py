import falcon
import pydash
from falcon import Request, Response
from marshmallow import Schema, fields

from ebl.dispatcher import create_dispatcher
from ebl.fragment.transliteration import Transliteration
from ebl.fragmentarium.fragmentarium import Fragmentarium
from ebl.require_scope import require_scope


class FragmentInfoSchema(Schema):
    number = fields.String()
    accession = fields.String()
    script = fields.String()
    description = fields.String()
    matching_lines = fields.List(
        fields.List(fields.String()),
        data_key="matchingLines"
    )


class FragmentSearch:
    def __init__(self, fragmentarium: Fragmentarium):
        self._dispatch = create_dispatcher({
            'number': fragmentarium.search,
            'random': lambda _: fragmentarium.find_random(),
            'interesting': lambda _: fragmentarium.find_interesting(),
            'latest': lambda _: fragmentarium.find_latest(),
            'transliteration': pydash.flow(
                Transliteration,
                fragmentarium.search_signs
            )
        })

    @falcon.before(require_scope, 'read:fragments')
    def on_get(self, req: Request, resp: Response) -> None:
        """Endpoint for querying fragments
        ---
        get:
          description: >-
            Finds fragments matching the given query.
            Exactly one query parameter must be given.

          responses:
            200:
              description: Fragments matching the query
              content:
                application/json:
                  schema:
                    type: array
                    items:
                      $ref: '#/components/schemas/FragmentInfo'
            422:
              description: Incorrect number of query parameters
          parameters:
          - in: query
            name: number
            schema:
              type: string
          - in: query
            name: random
            schema:
              type: boolean
          - in: query
            name: interesting
            schema:
              type: boolean
          - in: query
            name: latest
            schema:
              type: boolean
          - in: query
            name: transliteration
            schema:
              type: string
        """
        infos = self._dispatch(req.params)
        resp.media = FragmentInfoSchema(many=True).dump(infos)
