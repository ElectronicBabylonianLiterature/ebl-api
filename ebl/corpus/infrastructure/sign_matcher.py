from typing import List, Dict
from ebl.common.query.util import ngrams


class SignMatcher:
    def __init__(self, pattern: List[str]):
        self.pattern = pattern

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
                                "signs": {"$arrayElemAt": ["$$m", 1]},
                            },
                        }
                    },
                    "textId": 1,
                    "stage": 1,
                    "name": 1,
                    "manuscriptLines": "$lines.variants.manuscripts",
                }
            },
        ]

    def _restructure_signs(self) -> List[Dict]:
        return [
            {"$unwind": "$manuscriptWithSigns"},
            {
                "$project": {
                    "signs": {"$split": ["$manuscriptWithSigns.signs", "\n"]},
                    "manuscriptIdsToInclude": "$manuscriptWithSigns.manuscriptId",
                    "textId": True,
                    "stage": True,
                    "name": True,
                    "manuscriptLines": True,
                }
            },
            {
                "$unwind": {
                    "path": "$signs",
                    "includeArrayIndex": "manuscriptLinesToInclude",
                }
            },
        ]

    def _match(self) -> List[Dict]:
        # TODO: Construct proper ngram matching
        return [
            {"$match": {"signs": {"$regex": r"^X.*X$"}}},
            {
                "$project": {"signs": 0},
            },
        ]

    def _merge_manuscripts_to_include(self) -> List[Dict]:
        return [
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

    def _create_ngrams(self) -> List[Dict]:
        return [
            {"$unwind": "$manuscript"},
            {
                "$project": {
                    "ngram": ngrams("$manuscript.signs", len(self.pattern)),
                    "manuscriptId": "$manuscript.id",
                    "lines": True,
                }
            },
            {"$unwind": "$ngram"},
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

    def _regroup_chapters(self) -> List[Dict]:
        return [
            {
                "$group": {
                    "_id": "$_id",
                    "textId": {"$first": "$textId"},
                    "name": {"$first": "$name"},
                    "stage": {"$first": "$stage"},
                    "lineIndex": {"$push": "$lineIndex"},
                    "variantIndex": {"$push": "$variantIndex"},
                }
            }
        ]

    def build_pipeline(self) -> List[Dict]:
        pipeline = [
            *self._merge_manuscripts_and_signs(),
            *self._restructure_signs(),
            *self._match(),
            *self._merge_manuscripts_to_include(),
            *self._flatten_variants(),
            *self._filter_textlines(),
            *self._get_matching_variants(),
        ]
        return pipeline
