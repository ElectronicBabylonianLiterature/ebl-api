from pymongo.database import Database
from ebl.errors import NotFoundError

from ebl.mongo_collection import MongoCollection
from ebl.transliteration.application.parallel_line_injector import (
    ParallelRepository,
)
from ebl.transliteration.application.parallel_line_schemas import ChapterNameSchema
from ebl.transliteration.domain.museum_number import MuseumNumber
from ebl.transliteration.domain.parallel_line import (
    ChapterName,
)
from ebl.transliteration.domain.text_id import TextId
from ebl.transliteration.infrastructure.collections import (
    CHAPTERS_COLLECTION,
    FRAGMENTS_COLLECTION,
)
from ebl.transliteration.infrastructure.queries import query_number_is


class MongoParallelRepository(ParallelRepository):
    _fragments: MongoCollection
    _chapters: MongoCollection

    def __init__(self, database: Database):
        self._fragments = MongoCollection(database, FRAGMENTS_COLLECTION)
        self._chapters = MongoCollection(database, CHAPTERS_COLLECTION)

    def fragment_exists(self, museum_number: MuseumNumber) -> bool:
        return self._fragments.count_documents(query_number_is(museum_number)) > 0

    def find_implicit_chapter(self, text_id: TextId) -> ChapterName:
        try:
            chapter = next(
                self._chapters.find_many(
                    {
                        "textId.genre": text_id.genre.value,
                        "textId.category": text_id.category,
                        "textId.index": text_id.index,
                    },
                    sort=[("order", 1)],
                    projection={
                        "_id": False,
                        "stage": True,
                        "name": True,
                        "version": True,
                    },
                )
            )
            return ChapterNameSchema().load(chapter)
        except StopIteration as error:
            raise NotFoundError(f"No chapters found for text {text_id}.") from error

    def chapter_exists(self, text_id: TextId, chapter_name: ChapterName) -> bool:
        return (
            self._chapters.count_documents(
                {
                    "textId.genre": text_id.genre.value,
                    "textId.category": text_id.category,
                    "textId.index": text_id.index,
                    "stage": chapter_name.stage.long_name,
                    "name": chapter_name.name,
                }
            )
            > 0
        )
