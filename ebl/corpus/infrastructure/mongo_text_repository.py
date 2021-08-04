from typing import List

import pymongo

from ebl.bibliography.infrastructure.bibliography import join_reference_documents
from ebl.corpus.application.corpus import TextRepository
from ebl.corpus.domain.chapter import Chapter, ChapterId
from ebl.corpus.domain.manuscript import Manuscript
from ebl.corpus.domain.text import Text, TextId
from ebl.errors import NotFoundError
from ebl.mongo_collection import MongoCollection
from ebl.transliteration.domain.transliteration_query import TransliterationQuery
from ebl.corpus.application.schemas import ChapterSchema, TextSchema


TEXTS_COLLECTION = "texts"
CHAPTERS_COLLECTION = "chapters"


def text_not_found(id_: TextId) -> Exception:
    return NotFoundError(f"Text {id_} not found.")


def chapter_not_found(id_: ChapterId) -> Exception:
    return NotFoundError(f"Chapter {id_} not found.")


def chapter_id_query(id_: ChapterId) -> dict:
    return {
        "textId.genre": id_.text_id.genre.value,
        "textId.category": id_.text_id.category,
        "textId.index": id_.text_id.index,
        "stage": id_.stage.value,
        "name": id_.name,
    }


def join_chapters() -> List[dict]:
    return [
        {
            "$lookup": {
                "from": CHAPTERS_COLLECTION,
                "let": {"genre": "$genre", "category": "$category", "index": "$index"},
                "pipeline": [
                    {
                        "$match": {
                            "$expr": {
                                "$and": [
                                    {"$eq": ["$textId.genre", "$$genre"]},
                                    {"$eq": ["$textId.category", "$$category"]},
                                    {"$eq": ["$textId.index", "$$index"]},
                                ]
                            }
                        }
                    },
                    {"$sort": {"order": 1}},
                    {"$project": {"_id": 0, "stage": 1, "name": 1}},
                ],
                "as": "chapters",
            }
        },
        {"$project": {"_id": 0}},
    ]


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
                        *join_chapters(),
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
                    *join_chapters(),
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
        return []
