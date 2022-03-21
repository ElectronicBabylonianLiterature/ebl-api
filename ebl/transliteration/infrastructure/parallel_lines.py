from typing import Dict, Sequence

from pymongo.database import Database

from ebl.mongo_collection import MongoCollection
from ebl.transliteration.application.parallel_line_injector import (
    ParalallelLineInjector,
)
from ebl.transliteration.domain.parallel_line import ParallelFragment, ParallelText
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

    def _inject(
        self,
        line: dict,
    ) -> dict:
        if line["type"] == ParallelFragment.__name__:
            return {
                **line,
                "exists": self._fragments.count_documents(
                    museum_number_is(line["museumNumber"])
                )
                > 0,
            }
        elif line["type"] == ParallelText.__name__:
            if line.get("chapter") is None:
                try:
                    chapter = next(
                        self._chapters.find_many(
                            {
                                "textId.genre": line["text"]["genre"],
                                "textId.category": line["text"]["category"],
                                "textId.index": line["text"]["index"],
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
                    return {
                        **line,
                        "exists": True,
                        "implicitChapter": chapter,
                    }
                except (StopIteration, IndexError):
                    return {
                        **line,
                        "exists": False,
                    }
            else:
                return {
                    **line,
                    "exists": self._chapters.count_documents(
                        {
                            "textId.genre": line["text"]["genre"],
                            "textId.category": line["text"]["category"],
                            "textId.index": line["text"]["index"],
                            "stage": line["chapter"]["stage"],
                            "name": line["chapter"]["name"],
                        }
                    )
                    > 0,
                }
        else:
            return line

    def inject_exists(
        self,
        lines: Sequence[Dict],
    ) -> Sequence[Dict]:
        return list(map(self._inject, lines))
