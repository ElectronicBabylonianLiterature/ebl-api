from typing import List, Dict
from ebl.fragmentarium.infrastructure.fragment_lemma_matcher import flatten_field


class SignMatcher:
    def __init__(self, pattern: List[str]):
        self.pattern = pattern
        self._pattern_length = len(pattern)
        self._is_complex = self._pattern_length > 1

    def _match_transliteration_lines(self) -> List[Dict]:
        return [
            {
                "$addFields": {
                    "signChunks": {
                        "$zip": {
                            "inputs": [
                                "$signLines",
                                *(
                                    {
                                        "$slice": [
                                            "$signLines",
                                            i + 1,
                                            {"$size": "$signLines"},
                                        ]
                                    }
                                    for i in range(self._pattern_length - 1)
                                ),
                            ]
                        }
                    }
                }
            },
            {"$unwind": {"path": "$signChunks", "includeArrayIndex": "chunkIndex"}},
            {
                "$match": {
                    f"signChunks.{i}": {"$regex": line_pattern}
                    for i, line_pattern in enumerate(self.pattern)
                }
            },
        ]

    def _expand_line_ranges(self) -> Dict:
        return {
            "$map": {
                "input": {
                    "$range": [
                        "$chunkIndex",
                        {
                            "$add": [
                                "$chunkIndex",
                                self._pattern_length,
                            ]
                        },
                    ]
                },
                "as": "index",
                "in": {"$arrayElemAt": ["$textLines", "$$index"]},
            }
        }

    def build_pipeline(self, count_matches_per_item=True) -> List[Dict]:
        return [
            {
                "$project": {
                    "museumNumber": True,
                    "lineTypes": "$text.lines.type",
                    "signs": True,
                }
            },
            {"$unwind": {"path": "$lineTypes", "includeArrayIndex": "lineIndex"}},
            {"$match": {"lineTypes": "TextLine"}},
            {
                "$group": {
                    "_id": "$_id",
                    "museumNumber": {"$first": "$museumNumber"},
                    "textLines": {"$push": "$lineIndex"},
                    "signLines": {"$first": {"$split": ["$signs", "\n"]}},
                }
            },
            *(
                self._match_transliteration_lines()
                if self._is_complex
                else [
                    {
                        "$unwind": {
                            "path": "$signLines",
                            "includeArrayIndex": "chunkIndex",
                        }
                    },
                    {
                        "$match": {
                            "signLines": {"$regex": self.pattern[0]},
                        }
                    },
                ]
            ),
            {
                "$group": {
                    "_id": "$_id",
                    "museumNumber": {"$first": "$museumNumber"},
                    "matchingLines": {
                        "$push": self._expand_line_ranges()
                        if self._is_complex
                        else {"$arrayElemAt": ["$textLines", "$chunkIndex"]}
                    },
                    **({"matchCount": {"$sum": 1}} if count_matches_per_item else {}),
                }
            },
            *(
                [{"$addFields": {"matchingLines": flatten_field("$matchingLines")}}]
                if self._is_complex
                else []
            ),
        ]
