from typing import Optional, Tuple, cast

from ebl.bibliography.application.reference_documents import hydrate_reference_documents
from ebl.corpus.application.schemas import (
    LineSchema,
    TextSchema,
)
from ebl.corpus.domain.chapter import Chapter, ChapterId
from ebl.corpus.domain.chapter_display import ChapterDisplay
from ebl.corpus.domain.chapter_revision import LEGACY_REVISION
from ebl.corpus.domain.line import Line
from ebl.corpus.domain.text import Text, TextId
from ebl.corpus.infrastructure.queries import (
    aggregate_chapter_display,
    chapter_id_query,
    join_chapters,
)
from ebl.corpus.infrastructure.mongo_text_repository_base import (
    REVISION_FIELD,
    MongoTextRepositoryBase,
    text_not_found,
    chapter_not_found,
    line_not_found,
)
from ebl.corpus.infrastructure.stored_manuscript_schemas import (
    StoredChapterSchema,
    StoredChapterDisplaySchema,
)
from ebl.errors import NotFoundError


class MongoTextRepositoryFind(MongoTextRepositoryBase):
    def find(self, id_: TextId) -> Text:
        try:
            mongo_text = next(
                self._texts.aggregate(
                    [
                        {
                            "$match": {
                                "genre": id_.genre.value,
                                "category": id_.category,
                                "index": id_.index,
                            }
                        },
                        *join_chapters(True),
                        {"$limit": 1},
                    ]
                )
            )
            hydrate_reference_documents([mongo_text], self._bibliography_repository)
            return cast(
                Text,
                TextSchema(
                    context={"provenance_service": self._provenance_service}
                ).load(mongo_text),
            )

        except StopIteration as error:
            raise text_not_found(id_) from error

    def find_chapter(self, id_: ChapterId) -> Chapter:
        try:
            chapter = self._chapters.find_one(
                chapter_id_query(id_),
                projection={"_id": False, "_cacheRevision": False},
            )
            return self._load_chapter(chapter)
        except NotFoundError as error:
            raise chapter_not_found(id_) from error

    def find_chapter_with_revision(self, id_: ChapterId) -> Tuple[Chapter, str]:
        try:
            chapter = self._chapters.find_one(
                chapter_id_query(id_), projection={"_id": False}
            )
            revision: Optional[str] = chapter.pop(REVISION_FIELD, None)
            return (
                self._load_chapter(chapter),
                LEGACY_REVISION if revision is None else revision,
            )
        except NotFoundError as error:
            raise chapter_not_found(id_) from error

    def _load_chapter(self, chapter: dict) -> Chapter:
        return cast(
            Chapter,
            StoredChapterSchema(
                context={"provenance_service": self._provenance_service}
            ).load(chapter),
        )

    def find_chapter_for_display(self, id_: ChapterId) -> ChapterDisplay:
        try:
            text = self.find(id_.text_id)
            chapters = self._chapters.aggregate(aggregate_chapter_display(id_))
            return cast(
                ChapterDisplay,
                StoredChapterDisplaySchema(
                    context={"provenance_service": self._provenance_service}
                ).load(
                    {
                        **next(chapters),
                        "textName": text.name,
                        "textHasDoi": text.has_doi,
                        "isSingleStage": not text.has_multiple_stages,
                    }
                ),
            )
        except NotFoundError as error:
            raise text_not_found(id_.text_id) from error
        except StopIteration as error:
            raise chapter_not_found(id_) from error

    def find_line(self, id_: ChapterId, number: int) -> Line:
        try:
            chapters = self._chapters.aggregate(
                [
                    {"$match": chapter_id_query(id_)},
                    {"$unwind": "$lines"},
                    {"$replaceRoot": {"newRoot": "$lines"}},
                    {"$skip": number},
                ]
            )
            return cast(Line, LineSchema().load(next(chapters)))
        except StopIteration as error:
            raise line_not_found(id_, number) from error
