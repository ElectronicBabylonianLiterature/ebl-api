from typing import cast

import falcon
from marshmallow import Schema, fields, post_load
from marshmallow.validate import Length

from ebl.cache.application.custom_cache import ChapterCache
from ebl.corpus.application.chapter_edit_reader import ChapterEditReader
from ebl.corpus.application.chapter_edit_writer import ChapterEditWriter
from ebl.corpus.application.lines_pagination import (
    parse_required_text,
    parse_revision,
)
from ebl.corpus.domain.word_instances import WordLemma
from ebl.corpus.web.saved_chapter import RevisionSaveResponder
from ebl.corpus.web.text_utils import create_chapter_id
from ebl.marshmallowschema import validate
from ebl.users.web.require_scope import require_scope
from ebl.users.web.user_request import UserRequest

WORD_PARAMETER = "word"


class WordLemmaSchema(Schema):
    word = fields.String(required=True, validate=Length(min=1))
    unique_lemma = fields.List(
        fields.String(validate=Length(min=1)),
        required=True,
        validate=Length(min=1),
        data_key="uniqueLemma",
    )

    @post_load
    def make_word_lemma(self, data: dict, **kwargs: object) -> WordLemma:
        return WordLemma(data["word"], data["unique_lemma"])


class WordInstancesSchema(Schema):
    word = fields.String(required=True)
    words = fields.Integer(required=True)
    lemmatized = fields.Integer(required=True)
    lines = fields.List(fields.Integer(), required=True)
    revision = fields.String(required=True)


class WordInstancesResource:
    def __init__(
        self, writer: ChapterEditWriter, cache: ChapterCache, reader: ChapterEditReader
    ) -> None:
        self._writer = writer
        self._responder = RevisionSaveResponder(cache)
        self._reader = reader

    def on_get(
        self, req: falcon.Request, resp: falcon.Response, **chapter: str
    ) -> None:
        chapter_id = create_chapter_id(**chapter)
        word = parse_required_text(req.params, WORD_PARAMETER)
        revision = parse_revision(req.params)
        resp.media = WordInstancesSchema().dump(
            self._reader.find_word_instances(chapter_id, word, revision)
        )

    @falcon.before(require_scope, "write:texts")
    @validate(WordLemmaSchema())
    def on_post(self, req: UserRequest, resp: falcon.Response, **chapter: str) -> None:
        word_lemma = cast(WordLemma, WordLemmaSchema().load(req.media))
        self._responder.respond(
            req,
            resp,
            chapter,
            lambda chapter_id, revision, user: self._writer.save_word_lemma(
                chapter_id, word_lemma, revision, user
            ),
        )
