from typing import List, Dict
from ebl.common.query.util import ngrams, flatten_field


class CorpusSignMatcher:
    def __init__(self, pattern: List[str]):
        self.pattern = pattern
        self._pattern_length = len(self.pattern)
        self._is_multiline = self._pattern_length > 1

    def _merge_manuscripts_and_signs(self) -> List[Dict]:
        return [
            {
                "$project": {
                    "manuscriptsWithSigns": {
                        "$zip": {"inputs": ["$manuscripts.id", "$signs"]}
                    },
                    "textId": True,
                    "stage": True,
                    "name": True,
                    "lines.variants.manuscripts.manuscriptId": True,
                    "lines.variants.manuscripts.line.type": True,
                }
            },
            {
                "$project": {
                    "manuscriptWithSigns": {
                        "$map": {
                            "input": "$manuscriptsWithSigns",
                            "as": "m",
                            "in": {
                                "manuscriptId": {"$first": "$$m"},
                                "signs": {"$split": [{"$last": "$$m"}, "\n"]},
                            },
                        }
                    },
                    "textId": True,
                    "stage": True,
                    "name": True,
                    "lines": "$lines.variants.manuscripts",
                }
            },
            {
                "$unwind": {
                    "path": "$manuscriptWithSigns",
                }
            },
            {
                "$project": {
                    "textId": True,
                    "stage": True,
                    "name": True,
                    "manuscriptId": "$manuscriptWithSigns.manuscriptId",
                    "signs": "$manuscriptWithSigns.signs",
                    "lines": True,
                }
            },
        ]

    def _create_sign_line_ngrams(self) -> List[Dict]:
        return [
            {
                "$addFields": {
                    "ngram": ngrams("$signs", self._pattern_length),
                }
            },
        ]

    def _match_single_line(self) -> List[Dict]:
        return [
            {
                "$unwind": {
                    "path": "$signs",
                    "includeArrayIndex": "signLineIndex",
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
                    "includeArrayIndex": "signLineIndex",
                }
            },
            {
                "$match": {
                    f"ngram.{i}": {"$regex": line_pattern}
                    for i, line_pattern in enumerate(self.pattern)
                }
            },
        ]

    def _expand_line_ranges(self) -> Dict:
        return {
            "$range": [
                "$signLineIndex",
                {"$add": ["$signLineIndex", self._pattern_length]},
            ]
        }

    def _merge_manuscripts_to_include(self) -> List[Dict]:
        return [
            {
                "$group": {
                    "_id": {
                        "textId": "$textId",
                        "stage": "$stage",
                        "name": "$name",
                        "manuscriptId": "$manuscriptId",
                    },
                    "textLinesToInclude": {
                        "$push": (
                            self._expand_line_ranges()
                            if self._is_multiline
                            else "$signLineIndex"
                        )
                    },
                    "lines": {"$first": "$lines"},
                }
            },
        ]

    def _flatten_variants(self) -> List[Dict]:
        return [
            {"$unwind": {"path": "$lines", "includeArrayIndex": "lineIndex"}},
            {"$unwind": {"path": "$lines", "includeArrayIndex": "variantIndex"}},
        ]

    def _filter_textlines(self) -> List[Dict]:
        return [
            {
                "$addFields": {
                    "lines": {
                        "$filter": {
                            "input": "$lines",
                            "as": "line",
                            "cond": {
                                "$and": [
                                    {
                                        "$eq": [
                                            "$$line.manuscriptId",
                                            "$_id.manuscriptId",
                                        ]
                                    },
                                    {"$eq": ["$$line.line.type", "TextLine"]},
                                ]
                            },
                        }
                    }
                }
            },
            {"$match": {"lines": {"$exists": True, "$not": {"$size": 0}}}},
            {"$unwind": "$lines"},
        ]

    def _filter_line_variants_to_include(self) -> List[Dict]:
        return [
            {
                "$project": {
                    "lineVariantsToInclude": {
                        "$map": {
                            "input": {
                                "$filter": {
                                    "input": "$textLinesToInclude",
                                    "as": "i",
                                    "cond": {"$lt": ["$$i", "$_maxLength"]},
                                }
                            },
                            "as": "t",
                            "in": [
                                {"$arrayElemAt": ["$lineIndex", "$$t"]},
                                {"$arrayElemAt": ["$variantIndex", "$$t"]},
                            ],
                        }
                    }
                }
            },
            {"$unwind": "$lineVariantsToInclude"},
            {
                "$project": {
                    "lines": {"$first": "$lineVariantsToInclude"},
                    "variants": {"$last": "$lineVariantsToInclude"},
                }
            },
        ]

    def _deduplicate_matches(self) -> List[Dict]:
        return [
            {
                "$group": {
                    "_id": {
                        "textId": "$_id.textId",
                        "stage": "$_id.stage",
                        "name": "$_id.name",
                        "lines": "$lines",
                        "variants": "$variants",
                    }
                }
            },
            {"$replaceRoot": {"newRoot": "$_id"}},
            {"$sort": {"lines": 1, "variants": 1}},
        ]

    def _regroup_chapters(self, count_matches_per_item: bool) -> List[Dict]:
        return [
            {
                "$group": {
                    "_id": "$_id",
                    "_maxLength": {"$sum": 1},
                    "textLinesToInclude": {"$first": "$textLinesToInclude"},
                    "lineIndex": {"$push": "$lineIndex"},
                    "variantIndex": {"$push": "$variantIndex"},
                }
            },
            *self._filter_line_variants_to_include(),
            *self._deduplicate_matches(),
            {
                "$group": {
                    "_id": {
                        "textId": "$textId",
                        "stage": "$stage",
                        "name": "$name",
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
            *(
                [
                    {
                        "$addFields": {
                            "textLinesToInclude": flatten_field("$textLinesToInclude")
                        }
                    }
                ]
                if self._is_multiline
                else []
            ),
            *self._flatten_variants(),
            *self._filter_textlines(),
            *self._regroup_chapters(count_matches_per_item),
        ]
