from typing import List

import pymongo

from ebl.bibliography.infrastructure.bibliography import join_reference_documents
from ebl.corpus.application.corpus import TextRepository
from ebl.corpus.domain.chapter import Chapter, ChapterId
from ebl.corpus.domain.manuscript import Manuscript
from ebl.corpus.domain.text import Text, TextId
from ebl.corpus.infrastructure.collections import CHAPTERS_COLLECTION, TEXTS_COLLECTION
from ebl.corpus.infrastructure.queries import chapter_id_query, join_chapters
from ebl.errors import NotFoundError
from ebl.mongo_collection import MongoCollection
from ebl.transliteration.domain.transliteration_query import TransliterationQuery
from ebl.corpus.application.schemas import ChapterSchema, ManuscriptSchema, TextSchema
from ebl.fragmentarium.infrastructure.queries import is_in_fragmentarium, join_joins


def text_not_found(id_: TextId) -> Exception:
    return NotFoundError(f"Text {id_} not found.")


def chapter_not_found(id_: ChapterId) -> Exception:
    return NotFoundError(f"Chapter {id_} not found.")


class MongoTextRepository(TextRepository):
    def __init__(self, database):
        self._texts = MongoCollection(database, TEXTS_COLLECTION)
        self._chapters = MongoCollection(database, CHAPTERS_COLLECTION)

    def create_indexes(self) -> None:
        self._texts.create_index(
            [
                ("genre", pymongo.ASCENDING),
                ("category", pymongo.ASCENDING),
                ("index", pymongo.ASCENDING),
            ],
            unique=True,
        )
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

    def create(self, text: Text) -> None:
        self._texts.insert_one(TextSchema(exclude=["chapters"]).dump(text))

    def create_chapter(self, chapter: Chapter) -> None:
        self._chapters.insert_one(ChapterSchema().dump(chapter))

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
                        *join_reference_documents(),
                        *join_chapters(True),
                        {"$limit": 1},
                    ]
                )
            )
            return TextSchema().load(mongo_text)
        except StopIteration:
            raise text_not_found(id_)

    def find_chapter(self, id_: ChapterId) -> Chapter:
        try:
            chapter = self._chapters.find_one(
                chapter_id_query(id_), projection={"_id": False}
            )
            return ChapterSchema().load(chapter)
        except NotFoundError:
            raise chapter_not_found(id_)

    def list(self) -> List[Text]:
        return TextSchema().load(
            self._texts.aggregate(
                [
                    *join_reference_documents(),
                    *join_chapters(False),
                    {
                        "$sort": {
                            "category": pymongo.ASCENDING,
                            "index": pymongo.ASCENDING,
                        }
                    },
                ]
            ),
            many=True,
        )

    def update(self, id_: ChapterId, chapter: Chapter) -> None:
        self._chapters.update_one(
            chapter_id_query(id_),
            {
                "$set": ChapterSchema(
                    only=[
                        "manuscripts",
                        "uncertain_fragments",
                        "lines",
                        "signs",
                        "parser_version",
                    ]
                ).dump(chapter)
            },
        )

    def query_by_transliteration(self, query: TransliterationQuery) -> List[Chapter]:
        return ChapterSchema().load(
            self._chapters.find_many(
                {"signs": {"$regex": query.regexp}},
                projection={"_id": False},
                limit=100,
            ),
            many=True,
        )

    def query_manuscripts_by_chapter(self, id_: ChapterId) -> List[Manuscript]:
        try:
            return ManuscriptSchema().load(
                self._chapters.find_one(
                    chapter_id_query(id_), projection={"manuscripts": True}
                )["manuscripts"],
                many=True,
            )
        except NotFoundError:
            raise chapter_not_found(id_)

    def query_manuscripts_with_joins_by_chapter(
        self, id_: ChapterId
    ) -> List[Manuscript]:
        try:
            return ManuscriptSchema().load(
                self._chapters.aggregate(
                    [
                        {"$match": chapter_id_query(id_)},
                        {"$project": {"manuscripts": True}},
                        {"$unwind": "$manuscripts"},
                        {"$replaceRoot": {"newRoot": "$manuscripts"}},
                        *join_joins(),
                        *is_in_fragmentarium("museumNumber", "isInFragmentarium"),
                    ]
                ),
                many=True,
            )
        except NotFoundError:
            raise chapter_not_found(id_)
