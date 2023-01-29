from typing import List, Dict
from ebl.common.query.query_result import LemmaQueryType
from ebl.common.query.util import ngrams, drop_duplicates, flatten_field


def filter_array(input_, as_, cond) -> Dict:
    return {"$filter": {"input": input_, "as": as_, "cond": cond}}


class CorpusLemmaMatcher:
    reconstruction_lemma_path = "lines.variants.reconstruction.uniqueLemma"
    manuscriptlines_lemma_path = "lines.variants.manuscripts.line.content.uniqueLemma"
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
        _dispatcher = {
            LemmaQueryType.AND: self._and,
            LemmaQueryType.OR: self._or,
            LemmaQueryType.LINE: self._line,
            LemmaQueryType.PHRASE: self._phrase,
        }
        return _dispatcher[self.query_type](count_matches_per_item)

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

    def _unwind_lines(self) -> List[dict]:
        return [
            {"$unwind": {"path": "$lines", "includeArrayIndex": "lineIndex"}},
            {
                "$project": {
                    "variants": "$lines.variants",
                    "textId": 1,
                    "stage": 1,
                    "name": 1,
                    "lineIndex": 1,
                }
            },
        ]

    def _unwind_variants(self) -> List[dict]:
        return [
            {"$unwind": {"path": "$variants", "includeArrayIndex": "variantIndex"}},
            {
                "$project": {
                    "reconstruction": "$variants.reconstruction.uniqueLemma",
                    "flatReconstruction": flatten_field(
                        "$variants.reconstruction.uniqueLemma"
                    ),
                    "manuscripts": "$variants.manuscripts",
                    "textId": 1,
                    "stage": 1,
                    "name": 1,
                    "lineIndex": 1,
                    "variantIndex": 1,
                }
            },
        ]

    def _unwind_manuscripts(self) -> List[dict]:
        return [
            {
                "$unwind": {
                    "path": "$manuscripts",
                    "includeArrayIndex": "manuscriptLineIndex",
                }
            },
            {
                "$project": {
                    "reconstruction": 1,
                    "flatReconstruction": 1,
                    "manuscriptLine": "$manuscripts.line.content.uniqueLemma",
                    "flatManuscriptLine": flatten_field(
                        "$manuscripts.line.content.uniqueLemma"
                    ),
                    "textId": 1,
                    "stage": 1,
                    "name": 1,
                    "lineIndex": 1,
                    "variantIndex": 1,
                    "manuscriptLineIndex": 1,
                }
            },
        ]

    def _create_match_pipeline(
        self, chapter_query: Dict, line_query: Dict, count_matches_per_item=True
    ) -> List[Dict]:
        return [
            {"$match": chapter_query},
            {
                "$project": {
                    self.reconstruction_lemma_path: 1,
                    self.manuscriptlines_lemma_path: 1,
                    "textId": 1,
                    "stage": 1,
                    "name": 1,
                }
            },
            *self._unwind_lines(),
            *self._unwind_variants(),
            *self._unwind_manuscripts(),
            {"$match": line_query},
            *self._rejoin_lines(count_matches_per_item),
        ]

    @property
    def _lemma_paths(self) -> List[str]:
        return [self.reconstruction_lemma_path, self.manuscriptlines_lemma_path]

    @property
    def _flat_lemma_paths(self) -> List[str]:
        return ["flatReconstruction", "flatManuscriptLine"]

    def _lemma_path_combinations(self, flat=False) -> List[dict]:
        return [
            {path: lemma}
            for lemma in self.pattern
            for path in (self._flat_lemma_paths if flat else self._lemma_paths)
        ]

    def _and(self, count_matches_per_item=True) -> List[Dict]:
        return self._create_match_pipeline(
            {"$or": [{path: {"$all": self.pattern}} for path in self._lemma_paths]},
            {"$or": self._lemma_path_combinations(flat=True)},
            count_matches_per_item,
        )

    def _or(self, count_matches_per_item=True) -> List[Dict]:
        return self._create_match_pipeline(
            {"$or": self._lemma_path_combinations()},
            {"$or": self._lemma_path_combinations(flat=True)},
            count_matches_per_item,
        )

    def _line(self, count_matches_per_item=True) -> List[Dict]:
        return self._create_match_pipeline(
            {"$and": self._lemma_path_combinations()},
            {
                "$or": [
                    {"flatReconstruction": {"$all": self.pattern}},
                    {"flatManuscriptLine": {"$all": self.pattern}},
                ]
            },
        )

    def _phrase(self, count_matches_per_item=True) -> List[Dict]:
        return [
            {"$match": {"$and": self._lemma_path_combinations()}},
            {
                "$project": {
                    self.reconstruction_lemma_path: 1,
                    self.manuscriptlines_lemma_path: 1,
                    "textId": 1,
                    "stage": 1,
                    "name": 1,
                }
            },
            *self._unwind_lines(),
            *self._unwind_variants(),
            *self._unwind_manuscripts(),
            {
                "$match": {
                    "$or": [
                        {"flatReconstruction": {"$all": self.pattern}},
                        {"flatManuscriptLine": {"$all": self.pattern}},
                    ]
                }
            },
            {
                "$addFields": {
                    "reconstructionNgrams": filter_array(
                        drop_duplicates(
                            ngrams(f"${self.reconstruction_path}", n=len(self.pattern))
                        ),
                        "ngram",
                        {
                            "$and": [
                                {"$in": [lemma, {"$arrayElemAt": ["$$ngram", i]}]}
                                for i, lemma in enumerate(self.pattern)
                            ]
                        },
                    ),
                    "manuscriptLineNgrams": drop_duplicates(
                        ngrams("$manuscriptLine", n=len(self.pattern))
                    ),
                }
            },
        ]


if __name__ == "__main__":
    matcher = CorpusLemmaMatcher(["ša I", "pû I"], LemmaQueryType.PHRASE)
    import json

    print(json.dumps(matcher.build_pipeline(), indent=2))
