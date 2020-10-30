import falcon  # pyre-ignore[21]

from marshmallow import fields, Schema  # pyre-ignore[21]

from ebl.marshmallowschema import validate
from ebl.corpus.application.corpus import Corpus
from ebl.corpus.web.api_serializer import serialize
from ebl.corpus.web.text_utils import create_chapter_index, create_text_id
from ebl.transliteration.application.lemmatization_schema import (
    LemmatizationTokenSchema,
)
from ebl.users.web.require_scope import require_scope


class ManuscriptLemmatizationsSchema(Schema):  # pyre-ignore[11]
    lemmatization = fields.List(
        fields.List(fields.Nested(LemmatizationTokenSchema, many=True)), required=True
    )


class ManuscriptLemmatizationResource:
    def __init__(self, corpus: Corpus) -> None:
        self._corpus = corpus

    @falcon.before(require_scope, "write:texts")  # pyre-ignore[56]
    @validate(ManuscriptLemmatizationsSchema())
    def on_post(
        self,
        req: falcon.Request,  # pyre-ignore[11]
        resp: falcon.Response,  # pyre-ignore[11]
        category: str,
        index: str,
        chapter_index: str,
    ) -> None:
        self._corpus.update_manuscript_lemmatization(
            create_text_id(category, index),
            create_chapter_index(chapter_index),
            # pyre-ignore[16]
            ManuscriptLemmatizationsSchema().load(req.media)["lemmatization"],
            req.context.user,
        )
        updated_text = self._corpus.find(create_text_id(category, index))
        resp.media = serialize(updated_text)
