from typing import List, Dict
from ebl.common.query.util import flatten_field, ngrams


class SignMatcher:
    def __init__(self, pattern: List[str]):
        self.pattern = pattern
        self._pattern_length = len(pattern)
        self._is_multiline = self._pattern_length > 1

    def _match_multiline(self) -> List[Dict]:
        return [
            {"$addFields": {"ngram": ngrams("$signLines", self._pattern_length)}},
            {"$unwind": {"path": "$ngram", "includeArrayIndex": "ngramIndex"}},
            {
                "$match": {
                    f"ngram.{i}": {"$regex": line_pattern}
                    for i, line_pattern in enumerate(self.pattern)
                }
            },
        ]

    def _match_single_line(self) -> List[Dict]:
        return [
            {
                "$unwind": {
                    "path": "$signLines",
                    "includeArrayIndex": "signLineIndex",
                }
            },
            {
                "$match": {
                    "signLines": {"$regex": self.pattern[0]},
                }
            },
        ]

    def _expand_line_ranges(self) -> Dict:
        return {
            "$map": {
                "input": {
                    "$range": [
                        "$ngramIndex",
                        {
                            "$add": [
                                "$ngramIndex",
                                self._pattern_length,
                            ]
                        },
                    ]
                },
                "as": "index",
                "in": {"$arrayElemAt": ["$textLines", "$$index"]},
            }
        }

    def _map_signs_to_textlines(self) -> List[Dict]:
        return [
            {
                "$project": {
                    "museumNumber": True,
                    "_sortKey": True,
                    "script": True,
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
                    "_sortKey": {"$first": "$_sortKey"},
                    "script": {"$first": "$script"},
                    "textLines": {"$push": "$lineIndex"},
                    "signLines": {"$first": {"$split": ["$signs", "\n"]}},
                }
            },
        ]

    def build_pipeline(self, count_matches_per_item=True) -> List[Dict]:
        return [
            *self._map_signs_to_textlines(),
            *(
                self._match_multiline()
                if self._is_multiline
                else self._match_single_line()
            ),
            {
                "$group": {
                    "_id": "$_id",
                    "museumNumber": {"$first": "$museumNumber"},
                    "_sortKey": {"$first": "$_sortKey"},
                    "script": {"$first": "$script"},
                    "matchingLines": {
                        "$push": (
                            self._expand_line_ranges()
                            if self._is_multiline
                            else {"$arrayElemAt": ["$textLines", "$signLineIndex"]}
                        )
                    },
                    **({"matchCount": {"$sum": 1}} if count_matches_per_item else {}),
                }
            },
            *(
                [{"$addFields": {"matchingLines": flatten_field("$matchingLines")}}]
                if self._is_multiline
                else []
            ),
        ]
