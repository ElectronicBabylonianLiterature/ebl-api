from typing import List, Dict
from ebl.common.query.query_result import LemmaQueryType
from ebl.common.query.util import ngrams, drop_duplicates, flatten_field


class ManuscriptLemmaMatcher:
    lemma_path = "lines.variants.manuscripts.line.content.uniqueLemma"
    manuscript_line_path = "manuscriptLine"
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

    def _explode_manuscript_lines(self) -> List[Dict]:
        return [
            {"$unwind": {"path": "$lines", "includeArrayIndex": "lineIndex"}},
            {
                "$project": {
                    "lineIndex": 1,
                    self.manuscript_line_path: f"${self.lemma_path}",
                    "textId": 1,
                    "stage": 1,
                    "name": 1,
                }
            },
            {
                "$unwind": {
                    "path": f"${self.manuscript_line_path}",
                    "includeArrayIndex": "variantIndex",
                }
            },
            {"$unwind": f"${self.manuscript_line_path}"},
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
                    "matchCount": True,
                }
            },
        ]

    def _flatten_lemmas(self) -> List[dict]:
        return [
            {
                "$addFields": {
                    self.vocabulary_path: drop_duplicates(
                        flatten_field(f"${self.manuscript_line_path}")
                    )
                }
            }
        ]

    def _create_match_pipeline(
        self, chapter_query: Dict, line_query: Dict, count_matches_per_item=True
    ) -> List[Dict]:
        return [
            {"$match": chapter_query},
            *self._explode_manuscript_lines(),
            *self._flatten_lemmas(),
            {"$match": line_query},
            *self._rejoin_lines(count_matches_per_item),
        ]

    def _and(self, count_matches_per_item=True) -> List[Dict]:
        return self._create_match_pipeline(
            {self.lemma_path: {"$all": self.pattern}},
            {"$or": [{self.vocabulary_path: lemma} for lemma in self.pattern]},
            count_matches_per_item,
        )

    def _or(self, count_matches_per_item=True) -> List[Dict]:
        return self._create_match_pipeline(
            {self.lemma_path: {"$in": self.pattern}},
            {self.vocabulary_path: {"$in": self.pattern}},
            count_matches_per_item,
        )

    def _line(self, count_matches_per_item=True) -> List[Dict]:
        return self._create_match_pipeline(
            {self.lemma_path: {"$all": self.pattern}},
            {self.vocabulary_path: {"$all": self.pattern}},
            count_matches_per_item,
        )

    def _phrase(self, count_matches_per_item=True) -> List[Dict]:
        return [
            {"$match": {self.lemma_path: {"$all": self.pattern}}},
            *self._explode_manuscript_lines(),
            {
                "$match": {
                    self.manuscript_line_path: {"$not": {"$size": 0}, "$exists": True}
                }
            },
            {
                "$addFields": {
                    "ngram": ngrams(
                        f"${self.manuscript_line_path}", n=len(self.pattern)
                    ),
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
            *self._rejoin_lines(count_matches_per_item),
        ]