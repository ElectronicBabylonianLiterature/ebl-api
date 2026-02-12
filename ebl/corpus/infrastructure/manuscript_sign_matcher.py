from typing import List, Dict
from ebl.common.query.util import ngrams


class SignMatcher:
    def __init__(self, pattern: List[str]):
        self.pattern = pattern

    def _merge_manuscripts_and_signs(self) -> List[Dict]:
        _zip = {
            "$zip": {
                "inputs": [
                    "$manuscripts",
                    {
                        "$map": {
                            "input": "$signs",
                            "as": "signLine",
                            "in": {"signs": "$$signLine"},
                        }
                    },
                ]
            }
        }

        return [
            {
                "$project": {
                    "lines": True,
                    "manuscript": {
                        "$map": {
                            "input": _zip,
                            "as": "tuple",
                            "in": {"$mergeObjects": "$$tuple"},
                        }
                    },
                }
            },
        ]

    def _create_ngrams(self) -> List[Dict]:
        return [
            {"$unwind": "$manuscript"},
            {"$match": {"manuscript.signs": {"$exists": True, "$not": {"$size": 0}}}},
            {
                "$project": {
                    "ngram": ngrams("$manuscript.signs", len(self.pattern)),
                    "manuscriptId": "$manuscript.id",
                    "lines": True,
                }
            },
            {"$unwind": "$ngram"},
        ]

    def _collect_indexes(self) -> List[Dict]:
        return [
            {"$unwind": {"path": "$lines", "includeArrayIndex": "lineIndex"}},
            {
                "$unwind": {
                    "path": "$lines.variants",
                    "includeArrayIndex": "variantIndex",
                }
            },
            {
                "$project": {
                    "manuscriptLineIds": {
                        "$filter": {
                            "input": "$lines.variants.manuscripts",
                            "as": "manuscript",
                            "cond": {
                                "$eq": ["$$manuscript.manuscriptId", "$manuscriptId"]
                            },
                        }
                    },
                    "lineIndex": True,
                    "variantIndex": True,
                    "manuscriptId": True,
                }
            },
            {"$match": {"manuscriptLineIds": {"$exists": True, "$not": {"$size": 0}}}},
            {
                "$group": {
                    "_id": "$_id",
                    "manuscriptsToInclude": {"$addToSet": "$manuscriptId"},
                    "lineIndex": {"$push": "$lineIndex"},
                    "variantIndex": {"$push": "$variantIndex"},
                }
            },
        ]

    def build_pipeline(self) -> List[Dict]:
        return [
            {
                "$project": {
                    "manuscripts.id": True,
                    "signs": True,
                    "lines.variants.manuscripts.manuscriptId": True,
                }
            },
            *self._merge_manuscripts_and_signs(),
            *self._create_ngrams(),
            {
                "$match": {
                    f"ngram.{i}": {"$regex": line_pattern}
                    for i, line_pattern in enumerate(self.pattern)
                }
            },
            *self._collect_indexes(),
        ]
