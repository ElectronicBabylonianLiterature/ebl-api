from marshmallow import (  # pyre-ignore[21]
    fields,
    pre_load,
    post_dump,
    post_load,
    Schema,
)

from ebl.transliteration.domain.lemmatization import Lemmatization, LemmatizationToken


class LemmatizationTokenSchema(Schema):  # pyre-ignore[11]
    value = fields.String(required=True)
    unique_lemma = fields.List(fields.String, missing=None, data_key="uniqueLemma")

    @post_load
    def make_token(self, data, **kwargs):
        unique_lemma = (
            tuple(data["unique_lemma"]) if data["unique_lemma"] is not None else None
        )
        return LemmatizationToken(data["value"], unique_lemma)


class LemmatizationSchema(Schema):
    tokens = fields.List(
        fields.Nested(LemmatizationTokenSchema, many=True), required=True
    )

    @post_dump
    def extract_tokens(self, data, **kwargs):
        return data["tokens"]

    @pre_load
    def wrap_tokens(self, data, **kwargs):
        return {"tokens": data}

    @post_load
    def make_lemmatization(self, data, **kwargs):
        return Lemmatization(tuple(tuple(line) for line in data["tokens"]))
