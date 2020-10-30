import falcon  # pyre-ignore[21]
from marshmallow import Schema, post_load  # pyre-ignore[21]

from ebl.marshmallowschema import validate
from ebl.fragmentarium.application.fragment_updater import FragmentUpdater
from ebl.fragmentarium.web.dtos import create_response_dto, parse_museum_number
from ebl.users.web.require_scope import require_scope
from ebl.transliteration.application.lemmatization_schema import (
    LemmatizationTokenSchema,
)
from marshmallow import fields
from ebl.transliteration.domain.lemmatization import Lemmatization


class LemmatizationSchema(Schema):  # pyre-ignore[11]
    tokens = fields.List(
        fields.Nested(LemmatizationTokenSchema, many=True),
        required=True,
        data_key="lemmatization",
    )

    @post_load
    def make_lemmatization(self, data, **kwargs):
        return Lemmatization(tuple(tuple(line) for line in data["tokens"]))


class LemmatizationResource:
    def __init__(self, updater: FragmentUpdater):
        self._updater = updater

    @falcon.before(require_scope, "lemmatize:fragments")
    @validate(LemmatizationSchema())
    def on_post(self, req, resp, number):
        user = req.context.user
        updated_fragment, has_photo = self._updater.update_lemmatization(
            parse_museum_number(number), LemmatizationSchema().load(req.media), user
        )
        resp.media = create_response_dto(updated_fragment, user, has_photo)
