from typing import cast

import falcon
from marshmallow import Schema, post_load
from marshmallow import fields

from ebl.fragmentarium.application.fragment_updater import FragmentUpdater
from ebl.fragmentarium.web.dtos import FragmentDtoFactory, parse_museum_number
from ebl.lemmatization.domain.lemmatization import Lemmatization
from ebl.users.domain.user import User
from ebl.marshmallowschema import validate
from ebl.transliteration.application.lemmatization_schema import (
    LemmatizationTokenSchema,
)
from ebl.users.web.require_scope import require_scope


class LemmatizationSchema(Schema):
    tokens = fields.List(
        fields.Nested(LemmatizationTokenSchema, many=True),
        required=True,
        data_key="lemmatization",
    )

    @post_load
    def make_lemmatization(self, data, **kwargs):
        return Lemmatization(tuple(tuple(line) for line in data["tokens"]))


class LemmatizationResource:
    def __init__(self, updater: FragmentUpdater, dto_factory: FragmentDtoFactory):
        self._updater = updater
        self._dto_factory = dto_factory

    @falcon.before(require_scope, "lemmatize:fragments")
    @validate(LemmatizationSchema())
    def on_post(self, req, resp, number):
        user: User = req.context["user"]
        updated_fragment, has_photo = self._updater.update_lemmatization(
            parse_museum_number(number),
            cast(Lemmatization, LemmatizationSchema().load(req.media)),
            user,
        )
        resp.media = self._dto_factory.create(updated_fragment, user, has_photo)
