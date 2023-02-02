from typing import List, Dict
from ebl.common.query.query_result import LemmaQueryType
from ebl.common.query.util import ngrams, drop_duplicates, flatten_field


class ReconstructionLemmaMatcher:
    reconstruction_lemma_path = "lines.variants.reconstruction.uniqueLemma"
    reconstruction_path = "reconstruction"
    vocabulary_path = "vocabulary"

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

    def _explode_reconstruction(self) -> List[Dict]:
        return [
            {"$unwind": {"path": "$lines", "includeArrayIndex": "lineIndex"}},
            {
                "$project": {
                    "lineIndex": 1,
                    "variants": "$lines.variants",
                    "textId": 1,
                    "stage": 1,
                    "name": 1,
                }
            },
            {"$unwind": {"path": "$variants", "includeArrayIndex": "variantIndex"}},
            {
                "$addFields": {
                    self.reconstruction_path: "$variants.reconstruction.uniqueLemma",
                }
            },
        ]

    def _rejoin_lines(self, count_matches_per_item=True) -> List[Dict]:
        return [
            {
                "$group": {
                    "_id": {
                        "stage": "$stage",
                        "name": "$name",
                        "textId": "$textId",
                    },
                    "lines": {"$push": "$lineIndex"},
                    "variants": {"$push": "$variantIndex"},
                    **({"matchCount": {"$sum": 1}} if count_matches_per_item else {}),
                }
            },
            {
                "$project": {
                    "_id": False,
                    "stage": "$_id.stage",
                    "name": "$_id.name",
                    "textId": "$_id.textId",
                    "lines": True,
                    "variants": True,
                    "matchCount": count_matches_per_item,
                }
            },
        ]

    def _flatten_lemmas(self) -> List[dict]:
        return [
            {
                "$addFields": {
                    self.vocabulary_path: drop_duplicates(
                        flatten_field(f"${self.reconstruction_path}")
                    )
                }
            }
        ]

    def _create_match_pipeline(
        self, chapter_query: Dict, line_query: Dict, count_matches_per_item=True
    ) -> List[Dict]:
        return [
            {"$match": chapter_query},
            *self._explode_reconstruction(),
            *self._flatten_lemmas(),
            {"$match": line_query},
            *self._rejoin_lines(count_matches_per_item),
        ]

    def _and(self, count_matches_per_item=True) -> List[Dict]:
        return self._create_match_pipeline(
            {self.reconstruction_lemma_path: {"$all": self.pattern}},
            {"$or": [{self.vocabulary_path: lemma} for lemma in self.pattern]},
            count_matches_per_item,
        )

    def _or(self, count_matches_per_item=True) -> List[Dict]:
        return self._create_match_pipeline(
            {self.reconstruction_lemma_path: {"$in": self.pattern}},
            {self.vocabulary_path: {"$in": self.pattern}},
            count_matches_per_item,
        )

    def _line(self, count_matches_per_item=True) -> List[Dict]:
        return self._create_match_pipeline(
            {self.reconstruction_lemma_path: {"$all": self.pattern}},
            {self.vocabulary_path: {"$all": self.pattern}},
            count_matches_per_item,
        )

    def _phrase(self, count_matches_per_item=True) -> List[Dict]:
        return [
            {"$match": {self.reconstruction_lemma_path: {"$all": self.pattern}}},
            *self._explode_reconstruction(),
            {
                "$match": {
                    self.reconstruction_path: {"$not": {"$size": 0}, "$exists": True}
                }
            },
            {
                "$addFields": {
                    "ngram": ngrams(
                        f"${self.reconstruction_path}", n=len(self.pattern)
                    ),
                    "lineIndex": True,
                    "museumNumber": True,
                }
            },
            {"$addFields": {"ngram": drop_duplicates("$ngram")}},
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
