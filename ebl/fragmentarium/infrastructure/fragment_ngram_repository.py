from ebl.errors import NotFoundError
from ebl.mongo_collection import MongoCollection
from ebl.transliteration.application.museum_number_schema import MuseumNumberSchema
from ebl.transliteration.domain.museum_number import MuseumNumber
from ebl.transliteration.infrastructure.collections import (
    FRAGMENT_NGRAM_COLLECTION,
    FRAGMENTS_COLLECTION,
)
from typing import Sequence, Set, Tuple

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
    ):
        return [
            {"$match": {f"museumNumber.{key}": value for key, value in number.items()}},
            {
                "$project": {
                    NGRAM_FIELD: {
                        "$split": [
                            replace_all("\n", " # "),
                            " ",
                        ]
                    }
                }
            },
            *aggregate_all_ngrams(f"${NGRAM_FIELD}", N, NGRAM_FIELD),
        ]

    def update_ngrams(
        self,
        number: dict,
        N: Sequence[int],
    ) -> None:
        aggregation = self.aggregate_fragment_ngrams(number, N)
        if data := next(
            self._fragments.aggregate(aggregation, allowDiskUse=True),
            None,
        ):
            try:
                self._ngrams.update_one(
                    {"_id": data["_id"]}, {"$set": {NGRAM_FIELD: data[NGRAM_FIELD]}}
                )
            except NotFoundError:
                self._ngrams.insert_one(data)

    def get_ngrams(self, id_: str) -> Set[Tuple[str]]:
        ngrams = self._ngrams.find_one_by_id(id_)[NGRAM_FIELD]

        return {tuple(ngram) for ngram in ngrams}

    def get_or_set_ngrams(self, id_: str, N: Sequence[int]) -> Set[Tuple[str]]:
        try:
            ngrams = self._ngrams.find_one_by_id(id_)[NGRAM_FIELD]
        except NotFoundError:
            self.update_ngrams(MuseumNumberSchema().dump(MuseumNumber.of(id_)), N)
            ngrams = self._ngrams.find_one_by_id(id_)[NGRAM_FIELD]

        return {tuple(ngram) for ngram in ngrams}
