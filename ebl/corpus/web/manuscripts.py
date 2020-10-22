from typing import Sequence

import falcon  # pyre-ignore[21]
from falcon.media.validators.jsonschema import validate  # pyre-ignore[21]

from ebl.corpus.web.alignments import create_chapter_index
from ebl.corpus.web.api_serializer import serialize
from ebl.corpus.web.text_utils import create_text_id
from ebl.corpus.web.texts import MANUSCRIPT_DTO_SCHEMA
from ebl.corpus.domain.text import Manuscript
from ebl.users.web.require_scope import require_scope
from ebl.errors import DataError
from ebl.corpus.application.schemas import ApiManuscriptSchema


MANUSCRIPTS_DTO_SCHEMA = {
    "type": "object",
    "properties": {"manuscripts": {"type": "array", "items": MANUSCRIPT_DTO_SCHEMA}},
    "required": ["manuscripts"],
}


def deserialize_manuscripts(manuscripts: Sequence[dict]) -> Sequence[Manuscript]:
    try:
        return tuple(
            ApiManuscriptSchema().load(manuscripts, many=True)  # pyre-ignore[16]
        )
    except ValueError as error:
        raise DataError(error)


class ManuscriptsResource:
    def __init__(self, corpus):
        self._corpus = corpus

    @falcon.before(require_scope, "write:texts")
    @validate(MANUSCRIPTS_DTO_SCHEMA)  # pyre-ignore[56]
    def on_post(
        self,
        req: falcon.Request,  # pyre-ignore[11]
        resp: falcon.Response,  # pyre-ignore[11]
        category: str,
        index: str,
        chapter_index: str,
    ) -> None:
        self._corpus.update_manuscripts(
            create_text_id(category, index),
            create_chapter_index(chapter_index),
            deserialize_manuscripts(req.media["manuscripts"]),
            req.context.user,
        )
        updated_text = self._corpus.find(create_text_id(category, index))
        resp.media = serialize(updated_text)
