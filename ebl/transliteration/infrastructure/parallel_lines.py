from functools import partial
from typing import Dict, Sequence

from ebl.mongo_collection import MongoCollection
from ebl.transliteration.domain.parallel_line import ParallelFragment, ParallelText
from ebl.transliteration.infrastructure.queries import museum_number_is


def _inject(line: dict, fragments: MongoCollection, chapters: MongoCollection) -> dict:
    if line["type"] == ParallelFragment.__name__:
        return {
            **line,
            "exists": fragments.count_documents(museum_number_is(line["museumNumber"]))
            > 0,
        }
    elif line["type"] == ParallelText.__name__:
        return {
            **line,
            "exists": chapters.count_documents(
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
    lines: Sequence[Dict], fragments: MongoCollection, chapters: MongoCollection
) -> Sequence[Dict]:
    return list(map(partial(_inject, fragments=fragments, chapters=chapters), lines))
