from ebl.errors import NotFoundError
from ebl.mongo_collection import MongoCollection
from ebl.transliteration.infrastructure.collections import (
    FRAGMENT_NGRAM_COLLECTION,
    FRAGMENTS_COLLECTION,
)
from typing import Optional, Sequence

from ebl.common.query.util import aggregate_all_ngrams, replace_all

NGRAM_FIELD = "ngram"


class FragmentNGramRepository:
    def __init__(self, database):
        self._fragments = MongoCollection(database, FRAGMENTS_COLLECTION)
        self._ngrams = MongoCollection(database, FRAGMENT_NGRAM_COLLECTION)

    def aggregate_fragment_ngrams(
        self,
        number: dict,
        N: Sequence[int],
        signs_to_exclude: Optional[Sequence[str]] = None,
    ):
        return [
            {"$match": {f"museumNumber.{key}": value for key, value in number.items()}},
            {
                "$project": {
                    f"{NGRAM_FIELD}s": {
                        "$split": [
                            replace_all("#", " # "),
                            " ",
                        ]
                    }
                }
            },
            *aggregate_all_ngrams(
                f"${NGRAM_FIELD}s", N, f"{NGRAM_FIELD}s", signs_to_exclude
            ),
        ]

    def update_ngrams(
        self,
        number: dict,
        N: Sequence[int],
        signs_to_exclude: Optional[Sequence[str]] = None,
    ) -> None:
        aggregation = self.aggregate_fragment_ngrams(number, N, signs_to_exclude)
        data = next(
            self._fragments.aggregate(aggregation, allowDiskUse=True),
            None,
        )
        if data:
            try:
                self._ngrams.update_one(
                    {"_id": data["_id"]}, {"$set": {"ngrams": data["ngrams"]}}
                )
            except NotFoundError:
                self._ngrams.insert_one(data)
