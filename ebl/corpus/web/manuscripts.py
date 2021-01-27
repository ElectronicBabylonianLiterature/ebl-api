import falcon  # pyre-ignore[21]
from marshmallow import Schema, fields  # pyre-ignore[21]

from ebl.corpus.web.alignments import create_chapter_index
from ebl.corpus.web.api_serializer import serialize
from ebl.corpus.web.text_schemas import ApiManuscriptSchema, MuseumNumberString
from ebl.corpus.web.text_utils import create_text_id
from ebl.marshmallowschema import validate
from ebl.users.web.require_scope import require_scope


class ManuscriptDtoSchema(Schema):  # pyre-ignore[11]
    manuscripts = fields.Nested(ApiManuscriptSchema, many=True, required=True)
    uncertain_fragments = fields.List(
        MuseumNumberString(), missing=tuple(), data_key="uncertainFragments"
    )


class ManuscriptsResource:
    def __init__(self, corpus):
        self._corpus = corpus

    @falcon.before(require_scope, "write:texts")  # pyre-ignore[56]
    @validate(ManuscriptDtoSchema())
    def on_post(
        self,
        req: falcon.Request,  # pyre-ignore[11]
        resp: falcon.Response,  # pyre-ignore[11]
        category: str,
        index: str,
        chapter_index: str,
    ) -> None:
        dto = ManuscriptDtoSchema().load(req.media)  # pyre-ignore[16]
        self._corpus.update_manuscripts(
            create_text_id(category, index),
            create_chapter_index(chapter_index),
            dto["manuscripts"],
            tuple(dto["uncertain_fragments"]),
            req.context.user,
        )
        updated_text = self._corpus.find(create_text_id(category, index))
        resp.media = serialize(updated_text)
