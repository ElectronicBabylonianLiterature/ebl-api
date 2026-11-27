from typing import Sequence, cast

import falcon
from marshmallow import Schema, ValidationError, fields, post_load, validate

from ebl.lemmatization.application.suggestion_finder import (
    LemmaQuery,
    SuggestionFinder,
)
from ebl.marshmallowschema import validate as validate_body

MAX_BATCH_SIZE = 200


class StrictBoolean(fields.Boolean):
    def _deserialize(self, value: object, attr: object, data: object, **kwargs) -> bool:
        if not isinstance(value, bool):
            raise ValidationError("Not a valid boolean.")
        return value


class LemmaQuerySchema(Schema):
    word = fields.String(required=True)
    is_normalized = StrictBoolean(required=True, data_key="isNormalized")

    @post_load
    def make_query(self, data: dict, **kwargs) -> LemmaQuery:
        return LemmaQuery(data["word"], data["is_normalized"])


class LemmaBatchSchema(Schema):
    words = fields.List(
        fields.Nested(LemmaQuerySchema),
        required=True,
        validate=validate.Length(min=1, max=MAX_BATCH_SIZE),
    )


class LemmaBatchSearch:
    def __init__(self, finder: SuggestionFinder) -> None:
        self._finder = finder

    @validate_body(LemmaBatchSchema())
    def on_post(self, req: falcon.Request, resp: falcon.Response) -> None:
        queries = cast(
            Sequence[LemmaQuery],
            cast(dict, LemmaBatchSchema().load(req.media))["words"],
        )
        suggestions = self._finder.find_lemmas_of_many(queries)
        resp.media = [
            {
                "word": query.word,
                "isNormalized": query.is_normalized,
                "lemmas": suggestions[index],
            }
            for index, query in enumerate(queries)
        ]
