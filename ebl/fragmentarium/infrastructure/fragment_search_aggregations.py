from typing import List, Dict, Sequence, Optional, Union
from ebl.common.domain.scopes import Scope
from ebl.fragmentarium.domain.record import RecordType
from ebl.fragmentarium.infrastructure.queries import number_is, match_user_scopes
from ebl.fragmentarium.infrastructure.fragment_lemma_matcher import LemmaMatcher
from ebl.common.query.query_result import LemmaQueryType
from ebl.fragmentarium.infrastructure.fragment_sign_matcher import SignMatcher
from ebl.transliteration.domain.museum_number import (
    PREFIX_ORDER,
    NUMBER_PREFIX_ORDER,
    DEFAULT_PREFIX_ORDER,
)
from pydash.arrays import compact

VOCAB_PATH = "vocabulary"
LEMMA_PATH = "text.lines.content.uniqueLemma"
LATEST_TRANSLITERATION_LIMIT: int = 50
LATEST_TRANSLITERATION_LINE_LIMIT: int = 3


def convert_to_int(input_: Union[str, dict], default=0) -> dict:
    return {"$convert": {"input": input_, "to": "int", "onError": default}}


def sort_by_museum_number(
    pre_sort_keys: Optional[dict] = None, post_sort_keys: Optional[dict] = None
) -> List[Dict]:
    sort_keys = [
        {
            "$cond": [
                {
                    "$regexMatch": {
                        "input": "$museumNumber.prefix",
                        "regex": r"^\d+$",
                    }
                },
                NUMBER_PREFIX_ORDER,
                {
                    "$switch": {
                        "branches": [
                            {
                                "case": {"$eq": ["$museumNumber.prefix", key]},
                                "then": value,
                            }
                            for key, value in PREFIX_ORDER.items()
                        ],
                        "default": DEFAULT_PREFIX_ORDER,
                    }
                },
            ]
        },
        convert_to_int("$museumNumber.prefix", 0),
        "$museumNumber.prefix",
        convert_to_int("$museumNumber.number", default=float("Inf")),
        "$museumNumber.number",
        convert_to_int("$museumNumber.suffix", default=float("Inf")),
        "$museumNumber.suffix",
    ]
    return [
        {"$addFields": {"tmpSortKeys": sort_keys}},
        {
            "$sort": {
                **(pre_sort_keys or {}),
                **{f"tmpSortKeys.{i}": 1 for i in range(len(sort_keys))},
                **(post_sort_keys or {}),
            }
        },
        {"$project": {"tmpSortKeys": False}},
    ]


class PatternMatcher:
    def __init__(self, query: Dict, user_scopes: Sequence[Scope] = tuple()):
        self._query = query
        self._scopes = user_scopes

        self._lemma_matcher = (
            LemmaMatcher(
                query["lemmas"],
                query.get("lemmaOperator", LemmaQueryType.AND),
            )
            if "lemmas" in query
            else None
        )

        self._sign_matcher = (
            SignMatcher(query["transliteration"])
            if "transliteration" in query
            else None
        )

    def _limit_result(self):
        return [{"$limit": self._query["limit"]}] if "limit" in self._query else []

    def _sort_by(self, sort_fields: Optional[Dict] = None) -> List[Dict]:
        return [{"$sort": sort_fields}] if sort_fields else []

    def _wrap_query_items_with_total(
        self, sort_fields: Optional[Dict] = None
    ) -> List[Dict]:
        return [
            *self._sort_by(sort_fields),
            *self._limit_result(),
            {"$project": {"_id": False, "script": False, "_sortKey": False}},
            {
                "$group": {
                    "_id": None,
                    "items": {"$push": "$$ROOT"},
                    "matchCountTotal": {"$sum": "$matchCount"},
                }
            },
            {"$project": {"_id": False}},
        ]

    def _filter_by_script(self) -> Dict:
        parameters = {
            "scriptPeriod": "script.period",
            "scriptPeriodModifier": "script.periodModifier",
        }

        return {
            path: self._query.get(parameter)
            for parameter, path in parameters.items()
            if self._query.get(parameter)
        }

    def _filter_by_genre(self) -> Dict:
        if genre := self._query.get("genre"):
            return {"genres.category": {"$all": genre}}
        return {}

    def _filter_by_project(self) -> Dict:
        return {"projects": project} if (project := self._query.get("project")) else {}

    def _filter_by_reference(self) -> Dict:
        if "bibId" not in self._query:
            return {}

        parameters = {"id": self._query["bibId"]}
        if "pages" in self._query:
            parameters["pages"] = {
                "$regex": rf".*?(^|[^\d]){self._query['pages']}([^\d]|$).*?"
            }
        return {"references": {"$elemMatch": parameters}}

    def _filter_by_traditional_references(self) -> Dict:
        if traditional_references := self._query.get("traditionalReferences"):
            return {
                "traditionalReferences": {"$elemMatch": {"$eq": traditional_references}}
            }
        return {}

    def _prefilter(self) -> List[Dict]:
        constraints = {
            "$and": compact(
                [
                    number_is(self._query["number"]) if "number" in self._query else {},
                    self._filter_by_genre(),
                    self._filter_by_project(),
                    self._filter_by_script(),
                    self._filter_by_reference(),
                    self._filter_by_traditional_references(),
                    match_user_scopes(self._scopes),
                ]
            ),
        }

        return [{"$match": constraints}] if constraints else []

    def _merge_pipelines(self) -> List[Dict]:
        return [
            {
                "$facet": {
                    "transliteration": self._sign_matcher.build_pipeline(
                        count_matches_per_item=False
                    ),
                    "lemmas": self._lemma_matcher.build_pipeline(
                        count_matches_per_item=False
                    ),
                }
            },
            {
                "$project": {
                    "combined": {"$concatArrays": ["$transliteration", "$lemmas"]}
                }
            },
            {"$unwind": "$combined"},
            {"$replaceRoot": {"newRoot": "$combined"}},
            {
                "$group": {
                    "_id": "$_id",
                    "matchingLines": {"$push": "$matchingLines"},
                    "museumNumber": {"$first": "$museumNumber"},
                    "_sortKey": {"$first": "$_sortKey"},
                },
            },
            {
                "$match": {
                    "matchingLines": {"$size": 2},
                }
            },
            {
                "$addFields": {
                    "matchingLines": {
                        "$setUnion": [
                            {"$arrayElemAt": ["$matchingLines", 0]},
                            {"$arrayElemAt": ["$matchingLines", 1]},
                        ]
                    }
                }
            },
            {"$addFields": {"matchCount": {"$size": "$matchingLines"}}},
            {"$match": {"matchCount": {"$gt": 0}}},
        ]

    def _latest(
        self,
    ) -> List[Dict]:
        tmp_record = "tmpRecord"
        return [
            {
                "$match": {
                    "record.type": RecordType.TRANSLITERATION.value,
                    **match_user_scopes(self._scopes),
                }
            },
            {
                "$project": {
                    tmp_record: {
                        "$filter": {
                            "input": "$record",
                            "as": "entry",
                            "cond": {
                                "$eq": [
                                    "$$entry.type",
                                    RecordType.TRANSLITERATION.value,
                                ]
                            },
                        }
                    },
                    "lineType": "$text.lines.type",
                    "museumNumber": 1,
                }
            },
            {"$sort": {f"{tmp_record}.date": -1}},
            {"$limit": LATEST_TRANSLITERATION_LIMIT},
            {
                "$unwind": {
                    "path": "$lineType",
                    "includeArrayIndex": "lineIndex",
                }
            },
            {"$match": {"lineType": "TextLine"}},
            {
                "$group": {
                    "_id": "$_id",
                    "museumNumber": {"$first": "$museumNumber"},
                    "matchingLines": {"$push": "$lineIndex"},
                    tmp_record: {"$first": f"${tmp_record}"},
                }
            },
            {"$sort": {f"{tmp_record}.date": -1}},
            {
                "$project": {
                    "_id": False,
                    "museumNumber": True,
                    "matchCount": {"$literal": 0},
                    "matchingLines": {
                        "$slice": [
                            "$matchingLines",
                            0,
                            LATEST_TRANSLITERATION_LINE_LIMIT,
                        ]
                    },
                }
            },
            *self._wrap_query_items_with_total(),
        ]

    def build_pipeline(self) -> List[Dict]:
        if self._query.get("latest"):
            return self._latest()

        pipeline = self._prefilter()

        if self._lemma_matcher and self._sign_matcher:
            pipeline.extend(self._merge_pipelines())
        elif self._lemma_matcher:
            pipeline.extend(self._lemma_matcher.build_pipeline())
        elif self._sign_matcher:
            pipeline.extend(self._sign_matcher.build_pipeline())
        else:
            pipeline.extend(
                [
                    {
                        "$project": {
                            "_id": True,
                            "museumNumber": True,
                            "matchingLines": [],
                            "matchCount": {"$literal": 0},
                            "script": True,
                        }
                    },
                ]
            )

        pipeline.extend(
            self._wrap_query_items_with_total(
                sort_fields={"script.sortKey": 1, "_sortKey": 1}
            )
        )

        return pipeline
