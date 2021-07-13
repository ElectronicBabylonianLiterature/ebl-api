import falcon
from ebl.corpus.web.chapter_schemas import (
    ApiChapterSchema,
    ApiManuscriptSchema,
    MuseumNumberString,
)
from ebl.corpus.web.text_utils import create_chapter_id
from ebl.marshmallowschema import validate
from ebl.users.web.require_scope import require_scope
from marshmallow import Schema, fields


class ManuscriptDtoSchema(Schema):
    manuscripts = fields.Nested(ApiManuscriptSchema, many=True, required=True)
    uncertain_fragments = fields.List(
        MuseumNumberString(), missing=tuple(), data_key="uncertainFragments"
    )


class ManuscriptsResource:
    def __init__(self, corpus):
        self._corpus = corpus

    @falcon.before(require_scope, "write:texts")
    @validate(ManuscriptDtoSchema())
    def on_post(
        self,
        req: falcon.Request,
        resp: falcon.Response,
        genre: str,
        category: str,
        index: str,
        stage: str,
        name: str,
    ) -> None:
        chapter_id = create_chapter_id(genre, category, index, stage, name)
        dto = ManuscriptDtoSchema().load(req.media)
        updated_chapter = self._corpus.update_manuscripts(
            chapter_id,
            dto["manuscripts"],
            tuple(dto["uncertain_fragments"]),
            req.context.user,
        )
        resp.media = ApiChapterSchema().dump(updated_chapter)
