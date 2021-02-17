import falcon
from marshmallow import Schema, fields

from ebl.corpus.web.api_serializer import serialize
from ebl.corpus.web.text_schemas import ApiManuscriptSchema, MuseumNumberString
from ebl.corpus.web.text_utils import create_chapter_id
from ebl.marshmallowschema import validate
from ebl.users.web.require_scope import require_scope


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
        category: str,
        index: str,
        chapter_index: str,
    ) -> None:
        chapter_id = create_chapter_id(category, index, chapter_index)
        dto = ManuscriptDtoSchema().load(req.media)
        self._corpus.update_manuscripts(
            chapter_id,
            dto["manuscripts"],
            tuple(dto["uncertain_fragments"]),
            req.context.user,
        )
        updated_text = self._corpus.find(chapter_id.text_id)
        resp.media = serialize(updated_text)
