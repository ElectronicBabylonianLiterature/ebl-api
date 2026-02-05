from marshmallow import Schema, fields, post_load

from ebl.lemmatization.domain.lemmatization import LemmatizationToken


class LemmatizationTokenSchema(Schema):
    value = fields.String(required=True)
    unique_lemma = fields.List(fields.String, load_default=None, data_key="uniqueLemma")

    @post_load
    def make_token(self, data, **kwargs):
        unique_lemma = (
            tuple(data["unique_lemma"]) if data["unique_lemma"] is not None else None
        )
        return LemmatizationToken(data["value"], unique_lemma)
