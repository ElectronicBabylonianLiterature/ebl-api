import falcon
from marshmallow import Schema, fields

from ebl.corpus.application.corpus import Corpus
from ebl.corpus.application.lemmatization_schema import LineVariantLemmatizationSchema
from ebl.corpus.web.chapter_schemas import ApiChapterSchema
from ebl.corpus.web.text_utils import create_chapter_id
from ebl.marshmallowschema import validate
from ebl.users.web.require_scope import require_scope


class CorpusLemmatizationsSchema(Schema):
    lemmatization = fields.List(
        fields.List(fields.Nested(LineVariantLemmatizationSchema)), required=True
    )


class LemmatizationResource:
    def __init__(self, corpus: Corpus) -> None:
        self._corpus = corpus

    @falcon.before(require_scope, "write:texts")
    @validate(CorpusLemmatizationsSchema())
    def on_post(
        self,
        req: falcon.Request,
        resp: falcon.Response,
        category: str,
        index: str,
        stage: str,
        name: str,
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
          name: stage
          schema:
            type: string
          required: true
        - in: path
          name: name
          schema:
            type: string
          required: true
        """
        chapter_id = create_chapter_id(category, index, stage, name)
        self._corpus.update_manuscript_lemmatization(
            chapter_id,
            CorpusLemmatizationsSchema().load(req.media)["lemmatization"],
            req.context.user,
        )
        updated_chapter = self._corpus.find_chapter(chapter_id)
        resp.media = ApiChapterSchema().dump(updated_chapter)
