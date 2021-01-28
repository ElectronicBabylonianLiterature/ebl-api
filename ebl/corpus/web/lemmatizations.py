import falcon  # pyre-ignore[21]

from marshmallow import fields, Schema  # pyre-ignore[21]

from ebl.marshmallowschema import validate
from ebl.corpus.application.corpus import Corpus
from ebl.corpus.web.api_serializer import serialize
from ebl.corpus.web.text_utils import create_chapter_id
from ebl.corpus.application.lemmatization_schema import LineVariantLemmatizationSchema
from ebl.users.web.require_scope import require_scope


class CorpusLemmatizationsSchema(Schema):  # pyre-ignore[11]
    lemmatization = fields.List(
        fields.List(fields.Nested(LineVariantLemmatizationSchema)), required=True
    )


class LemmatizationResource:
    def __init__(self, corpus: Corpus) -> None:
        self._corpus = corpus

    @falcon.before(require_scope, "write:texts")  # pyre-ignore[56]
    @validate(CorpusLemmatizationsSchema())
    def on_post(
        self,
        req: falcon.Request,  # pyre-ignore[11]
        resp: falcon.Response,  # pyre-ignore[11]
        category: str,
        index: str,
        chapter_index: str,
    ) -> None:
        """---
        description: Lemmatizes manuscript lines.
        requestBody:
          content:
            application/json:
              schema:
                $ref: '#/components/schemas/CorpusLemmatizations'
        responses:
          200:
            description: Lemmatization was updated succesfully.
            content:
              application/json:
                schema:
                  $ref: '#/components/schemas/CorpusText'
          422:
            description: Invalid lemmatization
        security:
        - auth0:
          - write:texts
        parameters:
        - in: path
          name: category
          schema:
            type: integer
          required: true
        - in: path
          name: index
          schema:
            type: integer
          required: true
        - in: path
          name: chapter_index
          schema:
            type: integer
          required: true
        """
        chapter_id = create_chapter_id(category, index, chapter_index)
        self._corpus.update_manuscript_lemmatization(
            chapter_id,
            # pyre-ignore[16]
            CorpusLemmatizationsSchema().load(req.media)["lemmatization"],
            req.context.user,
        )
        updated_text = self._corpus.find(chapter_id.text_id)
        resp.media = serialize(updated_text)
