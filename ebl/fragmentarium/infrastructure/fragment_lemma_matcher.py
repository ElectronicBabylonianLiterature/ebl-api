from enum import Enum
from typing import List, Dict


class QueryType(Enum):
    AND = "and"
    OR = "or"
    LINE = "line"
    PHRASE = "phrase"
    LEMMA = "lemma"


class LemmaMatcher:
    unique_lemma_path = "text.lines.content.uniqueLemma"
    vocabulary_path = "vocabulary"
    flat_path = "lemmas"

    def __init__(
        self,
        pattern: List[str],
        query_type: QueryType,
    ):
        self.pattern = pattern
        self.query_type = query_type

    def build_pipeline(self, count_matches_per_item=True) -> List[Dict]:
        pipelines = {
            QueryType.LEMMA: self._lemma,
            QueryType.AND: self._and,
            QueryType.OR: self._or,
            QueryType.LINE: self._line,
            QueryType.PHRASE: self._phrase,
        }
        return pipelines[self.query_type](count_matches_per_item)

    def _flatten_lemmas(self) -> List[dict]:
        return [
            {
                "$addFields": {
                    self.vocabulary_path: {
                        "$setIntersection": {
                            "$reduce": {
                                "input": f"${self.flat_path}",
                                "initialValue": [],
                                "in": {"$concatArrays": ["$$value", "$$this"]},
                            }
                        }
                    },
                }
            }
        ]

    def _explode_lines(self) -> List[dict]:
        return [
            {
                "$project": {
                    "museumNumber": 1,
                    self.flat_path: f"${self.unique_lemma_path}",
                }
            },
            {
                "$unwind": {
                    "path": f"${self.flat_path}",
                    "includeArrayIndex": "lineIndex",
                }
            },
        ]

    def _rejoin_lines(self, count_matches_per_item=True) -> List[Dict]:
        return [
            {
                "$group": {
                    "_id": "$_id",
                    "matchingLines": {"$push": "$lineIndex"},
                    "museumNumber": {"$first": "$museumNumber"},
                    **({"matchCount": {"$sum": 1}} if count_matches_per_item else {}),
                }
            },
        ]

    def _create_match_pipeline(
        self, fragment_query: Dict, line_query: Dict, count_matches_per_item=True
    ) -> List[Dict]:
        return [
            {"$match": fragment_query},
            *self._explode_lines(),
            *self._flatten_lemmas(),
            {"$match": line_query},
            *self._rejoin_lines(count_matches_per_item),
        ]

    def _lemma(self, count_matches_per_item=True) -> List[Dict]:
        lemma = self.pattern[0]
        return self._create_match_pipeline(
            {self.unique_lemma_path: lemma},
            {self.vocabulary_path: lemma},
            count_matches_per_item,
        )

    def _and(self, count_matches_per_item=True) -> List[Dict]:
        return self._create_match_pipeline(
            {self.unique_lemma_path: {"$all": self.pattern}},
            {"$or": [{self.vocabulary_path: lemma} for lemma in self.pattern]},
            count_matches_per_item,
        )

    def _or(self, count_matches_per_item=True) -> List[Dict]:
        return self._create_match_pipeline(
            {self.unique_lemma_path: {"$in": self.pattern}},
            {self.vocabulary_path: {"$in": self.pattern}},
            count_matches_per_item,
        )

    def _line(self, count_matches_per_item=True) -> List[Dict]:
        return self._create_match_pipeline(
            {self.unique_lemma_path: {"$all": self.pattern}},
            {self.vocabulary_path: {"$all": self.pattern}},
            count_matches_per_item,
        )

    def _phrase(self, count_matches_per_item=True) -> List[Dict]:
        return [
            {"$match": {self.unique_lemma_path: {"$all": self.pattern}}},
            *self._explode_lines(),
            {"$match": {self.flat_path: {"$ne": [], "$exists": True}}},
            {
                "$project": {
                    "ngram": {
                        "$zip": {
                            "inputs": [
                                f"${self.flat_path}",
                                *(
                                    {
                                        "$slice": [
                                            f"${self.flat_path}",
                                            i + 1,
                                            {"$size": f"${self.flat_path}"},
                                        ]
                                    }
                                    for i in range(len(self.pattern) - 1)
                                ),
                            ]
                        }
                    },
                    "lineIndex": True,
                    "museumNumber": True,
                }
            },
            {"$addFields": {"ngram": {"$setUnion": ["$ngram", []]}}},
            {"$unwind": "$ngram"},
            {
                "$match": {
                    "$expr": {
                        "$and": [
                            {"$in": [lemma, {"$arrayElemAt": ["$ngram", i]}]}
                            for i, lemma in enumerate(self.pattern)
                        ]
                    }
                }
            },
            *self._rejoin_lines(),
        ]
