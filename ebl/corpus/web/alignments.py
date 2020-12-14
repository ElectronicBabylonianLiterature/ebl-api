import falcon  # pyre-ignore[21]

from ebl.marshmallowschema import validate
from ebl.corpus.web.api_serializer import serialize
from ebl.corpus.web.text_utils import create_chapter_index, create_text_id
from ebl.users.web.require_scope import require_scope
from ebl.corpus.web.alignment_schema import AlignmentSchema


class AlignmentResource:
    def __init__(self, corpus):
        self._corpus = corpus

    @falcon.before(require_scope, "write:texts")  # pyre-ignore[56]
    @validate(AlignmentSchema())
    def on_post(
        self,
        req: falcon.Request,  # pyre-ignore[11]
        resp: falcon.Response,  # pyre-ignore[11]
        category: str,
        index: str,
        chapter_index: str,
    ) -> None:
        self._corpus.update_alignment(
            create_text_id(category, index),
            create_chapter_index(chapter_index),
            AlignmentSchema().load(req.media),  # pyre-ignore[16]
            req.context.user,
        )
        updated_text = self._corpus.find(create_text_id(category, index))
        resp.media = serialize(updated_text)
