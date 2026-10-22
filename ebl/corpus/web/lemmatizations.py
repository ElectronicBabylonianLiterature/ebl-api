import falcon
from typing import cast
from marshmallow import Schema, fields

from ebl.cache.application.custom_cache import ChapterCache
from ebl.corpus.application.corpus import Corpus
from ebl.corpus.application.lemmatization_schema import LineVariantLemmatizationSchema
from ebl.corpus.web.chapter_schemas import ApiChapterSchema
from ebl.corpus.web.text_utils import create_chapter_id
from ebl.marshmallowschema import validate
from ebl.users.web.require_scope import require_scope
from ebl.users.web.user_request import UserRequest


class CorpusLemmatizationsSchema(Schema):
    lemmatization = fields.List(
        fields.List(fields.Nested(LineVariantLemmatizationSchema)), required=True
    )


class LemmatizationResource:
    def __init__(self, corpus: Corpus, cache: ChapterCache) -> None:
        self._corpus = corpus
        self._cache = cache

    @falcon.before(require_scope, "write:texts")
    @validate(CorpusLemmatizationsSchema())
    def on_post(
        self,
        req: UserRequest,
        resp: falcon.Response,
        genre: str,
        category: str,
        index: str,
        stage: str,
        name: str,
    ) -> None:
        chapter_id = create_chapter_id(genre, category, index, stage, name)
        with self._cache.updating_chapter(chapter_id):
            updated_chapter = self._corpus.update_manuscript_lemmatization(
                chapter_id,
                cast(dict, CorpusLemmatizationsSchema().load(req.media))[
                    "lemmatization"
                ],
                req.context.user,
            )
        resp.media = ApiChapterSchema().dump(updated_chapter)
