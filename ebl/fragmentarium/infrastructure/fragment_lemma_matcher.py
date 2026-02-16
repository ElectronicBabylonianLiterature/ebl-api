from ebl.common.query.query_result import LemmaQueryType
from ebl.common.query.util import flatten_field, drop_duplicates, ngrams
from typing import List, Dict


class EmptyMatcher:
    def build_pipeline(self, *args, **kwargs) -> List[Dict]:
        return []

    def __bool__(self):
        return False


class LemmaMatcher:
    unique_lemma_path = "text.lines.content.uniqueLemma"
    vocabulary_path = "vocabulary"
    flat_path = "lemmas"

    def __init__(
        self,
        pattern: List[str],
        query_type: LemmaQueryType,
    ):
        self.pattern = pattern
        self.query_type = query_type

    def build_pipeline(self, count_matches_per_item=True) -> List[Dict]:
        pipelines = {
            LemmaQueryType.AND: self._and,
            LemmaQueryType.OR: self._or,
            LemmaQueryType.LINE: self._line,
            LemmaQueryType.PHRASE: self._phrase,
        }
        return pipelines[self.query_type](count_matches_per_item)

    def _flatten_lemmas(self) -> List[dict]:
        return [
            {
                "$addFields": {
                    self.vocabulary_path: drop_duplicates(
                        flatten_field(f"${self.flat_path}")
                    )
                }
            }
        ]

    def _explode_lines(self) -> List[dict]:
        return [
            {
                "$project": {
                    "museumNumber": 1,
                    "_sortKey": 1,
                    self.flat_path: f"${self.unique_lemma_path}",
                    "script": 1,
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
                    "_sortKey": {"$first": "$_sortKey"},
                    "script": {"$first": "$script"},
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
            {"$match": {self.flat_path: {"$not": {"$size": 0}, "$exists": True}}},
            {
                "$project": {
                    "ngram": ngrams(f"${self.flat_path}", n=len(self.pattern)),
                    "lineIndex": True,
                    "museumNumber": True,
                    "_sortKey": True,
                    "script": True,
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
            *self._rejoin_lines(count_matches_per_item),
        ]
