from marshmallow import Schema, fields, post_load

from ebl.corpus.application.lemmatization import LineVariantLemmatization
from ebl.transliteration.application.lemmatization_schema import (
    LemmatizationTokenSchema,
)


class LineVariantLemmatizationSchema(Schema):
    reconstruction = fields.Nested(LemmatizationTokenSchema, many=True, required=True)
    manuscripts = fields.List(
        fields.Nested(LemmatizationTokenSchema, many=True), required=True
    )

    @post_load
    def make_lemmatization(self, data, **kwargs):
        return LineVariantLemmatization(
            tuple(data["reconstruction"]),
            tuple(tuple(manuscript) for manuscript in data["manuscripts"]),
        )
