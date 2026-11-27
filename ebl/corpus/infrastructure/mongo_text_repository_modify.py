import pymongo
from bson import ObjectId
from typing import Callable, Mapping, cast
from ebl.corpus.application.schemas import (
    ChapterSchema,
    TextSchema,
)
from ebl.corpus.domain.chapter import Chapter, ChapterId
from ebl.corpus.domain.chapter_change import KEEP_NOTHING, KeptContent
from ebl.corpus.domain.line import Line
from ebl.corpus.domain.text import Text
from ebl.corpus.infrastructure.chapter_update_pipeline import (
    create_chapter_update,
    create_lines_update,
)
from ebl.corpus.infrastructure.queries import (
    chapter_id_query,
)
from ebl.corpus.infrastructure.mongo_text_repository_base import (
    REVISION_FIELD,
    MongoTextRepositoryBase,
    revision_query,
)
from ebl.corpus.domain.chapter_revision import chapter_revision_conflict
from ebl.errors import NotFoundError
from ebl.transliteration.application.storage_serialization import (
    storage_serialization,
)


class MongoTextRepositoryModify(MongoTextRepositoryBase):
    def _create_text_indexes(self) -> None:
        self._texts.create_index(
            [
                ("genre", pymongo.ASCENDING),
                ("category", pymongo.ASCENDING),
                ("index", pymongo.ASCENDING),
            ],
            unique=True,
        )
        self._texts.create_index([("category", pymongo.ASCENDING)])
        self._texts.create_index([("index", pymongo.ASCENDING)])

    def _create_chapter_indexes(self) -> None:
        self._chapters.create_index(
            [
                ("textId.genre", pymongo.ASCENDING),
                ("textId.category", pymongo.ASCENDING),
                ("textId.index", pymongo.ASCENDING),
            ]
        )
        self._chapters.create_index(
            [
                ("textId.genre", pymongo.ASCENDING),
                ("textId.category", pymongo.ASCENDING),
                ("textId.index", pymongo.ASCENDING),
                ("order", pymongo.ASCENDING),
            ]
        )
        self._chapters.create_index(
            [
                ("textId.genre", pymongo.ASCENDING),
                ("textId.category", pymongo.ASCENDING),
                ("textId.index", pymongo.ASCENDING),
                ("stage", pymongo.ASCENDING),
                ("name", pymongo.ASCENDING),
            ],
            unique=True,
        )
        self._chapters.create_index(
            [
                ("manuscripts.museumNumber.prefix", pymongo.ASCENDING),
                ("manuscripts.museumNumber.number", pymongo.ASCENDING),
                ("manuscripts.museumNumber.suffix", pymongo.ASCENDING),
            ]
        )
        self._chapters.create_index(
            [
                ("uncertainFragments.prefix", pymongo.ASCENDING),
                ("uncertainFragments.number", pymongo.ASCENDING),
                ("uncertainFragments.suffix", pymongo.ASCENDING),
            ]
        )

    def create_indexes(self) -> None:
        self._create_text_indexes()
        self._create_chapter_indexes()

    def create(self, text: Text) -> None:
        self._texts.insert_one(TextSchema(exclude=["chapters"]).dump(text))

    def create_chapter(self, chapter: Chapter) -> None:
        with storage_serialization():
            document = ChapterSchema().dump(chapter)
        self._chapters.insert_one(document)

    def _create_update(self, chapter: Chapter, revision: str) -> dict:
        with storage_serialization():
            update = cast(
                dict,
                ChapterSchema(
                    only=[
                        "manuscripts",
                        "uncertain_fragments",
                        "lines",
                        "signs",
                        "parser_version",
                    ]
                ).dump(chapter),
            )
        return {"$set": {**update, REVISION_FIELD: revision}}

    def update(self, id_: ChapterId, chapter: Chapter) -> str:
        revision = str(ObjectId())
        self._chapters.update_one(
            chapter_id_query(id_), self._create_update(chapter, revision)
        )
        return revision

    def update_at_revision(
        self,
        id_: ChapterId,
        chapter: Chapter,
        revision: str,
        kept: KeptContent = KEEP_NOTHING,
    ) -> str:
        return self._update_at_revision(
            id_,
            revision,
            lambda new_revision: create_chapter_update(chapter, kept, new_revision),
        )

    def update_lines_at_revision(
        self, id_: ChapterId, lines: Mapping[int, Line], revision: str
    ) -> str:
        return self._update_at_revision(
            id_, revision, lambda new_revision: create_lines_update(lines, new_revision)
        )

    def _update_at_revision(
        self, id_: ChapterId, revision: str, create_update: Callable[[str], object]
    ) -> str:
        new_revision = str(ObjectId())
        try:
            self._chapters.update_one(
                {**chapter_id_query(id_), **revision_query(revision)},
                create_update(new_revision),
            )
        except NotFoundError as error:
            stored_revision = self.find_chapter_revision(id_)
            if stored_revision != new_revision:
                raise chapter_revision_conflict(
                    id_, revision, stored_revision
                ) from error
        return new_revision
