from typing import List, Dict
from ebl.common.query.util import ngrams


class CorpusSignMatcher:
    def __init__(self, pattern: List[str]):
        self.pattern = pattern
        self._is_multiline = len(self.pattern) > 1

    def _merge_manuscripts_and_signs(self) -> List[Dict]:
        return [
            {
                "$project": {
                    "manuscriptsWithSigns": {
                        "$zip": {"inputs": ["$manuscripts.id", "$signs"]}
                    },
                    "textId": 1,
                    "stage": 1,
                    "name": 1,
                    "lines.variants.manuscripts.manuscriptId": 1,
                    "lines.variants.manuscripts.line.type": 1,
                }
            },
            {
                "$project": {
                    "manuscriptWithSigns": {
                        "$map": {
                            "input": "$manuscriptsWithSigns",
                            "as": "m",
                            "in": {
                                "manuscriptId": {"$arrayElemAt": ["$$m", 0]},
                                "signs": {
                                    "$split": [{"$arrayElemAt": ["$$m", 1]}, "\n"]
                                },
                            },
                        }
                    },
                    "textId": 1,
                    "stage": 1,
                    "name": 1,
                    "manuscriptLines": "$lines.variants.manuscripts",
                }
            },
            {"$unwind": "$manuscriptWithSigns"},
            {
                "$project": {
                    "manuscriptIdsToInclude": "$manuscriptWithSigns.manuscriptId",
                    "signs": "$manuscriptWithSigns.signs",
                    "textId": True,
                    "stage": True,
                    "name": True,
                    "manuscriptLines": True,
                }
            },
        ]

    def _create_sign_line_ngrams(self) -> List[Dict]:
        return [
            {
                "$addFields": {
                    "ngram": ngrams("$signs", len(self.pattern)),
                }
            },
        ]

    def _match_single_line(self) -> List[Dict]:
        return [
            {
                "$unwind": {
                    "path": "$signs",
                    "includeArrayIndex": "manuscriptLinesToInclude",
                }
            },
            {"$match": {"signs": {"$regex": self.pattern[0]}}},
        ]

    def _match_multiline(self) -> List[Dict]:
        return [
            *self._create_sign_line_ngrams(),
            {
                "$unwind": {
                    "path": "$ngram",
                    "includeArrayIndex": "manuscriptLinesToInclude",
                }
            },
            {
                "$match": {
                    f"ngram.{i}": {"$regex": line_pattern}
                    for i, line_pattern in enumerate(self.pattern)
                }
            },
        ]

    def _merge_manuscripts_to_include(self) -> List[Dict]:
        return [
            {
                "$project": {"signs": 0, "ngram": 0},
            },
            {
                "$group": {
                    "_id": "$_id",
                    "stage": {"$first": "$stage"},
                    "name": {"$first": "$name"},
                    "textId": {"$first": "$textId"},
                    "manuscriptIdsToInclude": {"$push": "$manuscriptIdsToInclude"},
                    "manuscriptLinesToInclude": {"$push": "$manuscriptLinesToInclude"},
                    "manuscriptId": {"$first": "$manuscriptLines"},
                }
            },
            {
                "$project": {
                    "manuscriptsToInclude": {
                        "$zip": {
                            "inputs": [
                                "$manuscriptIdsToInclude",
                                "$manuscriptLinesToInclude",
                            ]
                        }
                    },
                    "stage": 1,
                    "name": 1,
                    "textId": 1,
                    "manuscriptId": 1,
                }
            },
        ]

    def _flatten_variants(self) -> List[Dict]:
        return [
            {"$unwind": {"path": "$manuscriptId", "includeArrayIndex": "lineIndex"}},
            {"$unwind": {"path": "$manuscriptId", "includeArrayIndex": "variantIndex"}},
        ]

    def _filter_textlines(self) -> List[Dict]:
        return [
            {
                "$addFields": {
                    "manuscriptId": {
                        "$filter": {
                            "input": "$manuscriptId",
                            "as": "m",
                            "cond": {"$eq": ["$$m.line.type", "TextLine"]},
                        }
                    }
                }
            },
        ]

    def _get_matching_variants(self) -> List[Dict]:
        return [
            {
                "$unwind": {
                    "path": "$manuscriptId",
                    "includeArrayIndex": "manuscriptVariantLineIndex",
                }
            },
            {
                "$match": {
                    "$expr": {
                        "$in": [
                            [
                                "$manuscriptId.manuscriptId",
                                "$manuscriptVariantLineIndex",
                            ],
                            "$manuscriptsToInclude",
                        ]
                    }
                }
            },
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

    def _regroup_chapters(self, count_matches_per_item: bool) -> List[Dict]:
        return [
            {
                "$group": {
                    "_id": {
                        "textId": "$textId",
                        "name": "$name",
                        "stage": "$stage",
                        "lines": "$lineIndex",
                        "variants": "$variantIndex",
                    },
                }
            },
            {"$replaceRoot": {"newRoot": "$_id"}},
            {"$sort": {"lines": 1, "variants": 1}},
            {
                "$group": {
                    "_id": {
                        "textId": "$textId",
                        "name": "$name",
                        "stage": "$stage",
                    },
                    "lines": {"$push": "$lines"},
                    "variants": {"$push": "$variants"},
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
                    **({"matchCount": True} if count_matches_per_item else {}),
                }
            },
        ]

    def build_pipeline(self, count_matches_per_item=True) -> List[Dict]:
        return [
            *self._merge_manuscripts_and_signs(),
            *(
                self._match_multiline()
                if self._is_multiline
                else self._match_single_line()
            ),
            *self._merge_manuscripts_to_include(),
            *self._flatten_variants(),
            *self._filter_textlines(),
            *self._get_matching_variants(),
            *self._regroup_chapters(count_matches_per_item),
        ]
