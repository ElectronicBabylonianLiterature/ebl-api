from functools import singledispatchmethod
from typing import Sequence, cast

import attr
from pymongo.database import Database

from ebl.mongo_collection import MongoCollection
from ebl.transliteration.application.parallel_line_injector import (
    T,
    ParalallelLineInjector,
)
from ebl.transliteration.application.parallel_line_schemas import ChapterNameSchema
from ebl.transliteration.domain.parallel_line import (
    ChapterName,
    ParallelFragment,
    ParallelText,
)
from ebl.transliteration.infrastructure.collections import (
    CHAPTERS_COLLECTION,
    FRAGMENTS_COLLECTION,
)
from ebl.transliteration.infrastructure.queries import museum_number_is


class MongoParalallelLineInjector(ParalallelLineInjector):
    _fragments: MongoCollection
    _chapters: MongoCollection

    def __init__(self, database: Database):
        self._fragments = MongoCollection(database, FRAGMENTS_COLLECTION)
        self._chapters = MongoCollection(database, CHAPTERS_COLLECTION)

    @singledispatchmethod
    def _inject(self, line: T) -> T:
        return line

    @_inject.register(ParallelFragment)
    def _(self, line: ParallelFragment) -> ParallelFragment:
        return attr.evolve(
            line,
            exists=self._fragments.count_documents(museum_number_is(line.museum_number))
            > 0,
        )

    @_inject.register(ParallelText)
    def _(self, line: ParallelText) -> ParallelText:
        if line.chapter is None:
            try:
                chapter = next(
                    self._chapters.find_many(
                        {
                            "textId.genre": line.text.genre.value,
                            "textId.category": line.text.category,
                            "textId.index": line.text.index,
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
                return attr.evolve(
                    line,
                    exists=True,
                    implicit_chapter=ChapterNameSchema().load(chapter),
                )
            except (StopIteration, IndexError):
                return attr.evolve(line, exists=False)
        else:
            chapter = cast(ChapterName, line.chapter)
            return attr.evolve(
                line,
                exists=self._chapters.count_documents(
                    {
                        "textId.genre": line.text.genre.value,
                        "textId.category": line.text.category,
                        "textId.index": line.text.index,
                        "stage": chapter.stage.value,
                        "name": chapter.name,
                    }
                )
                > 0,
            )

    def inject_exists(self, lines: Sequence[T]) -> Sequence[T]:
        return tuple(self._inject(line) for line in lines)
