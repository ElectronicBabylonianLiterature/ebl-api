from typing import List, Dict, Sequence, Optional
from ebl.common.domain.scopes import Scope
from ebl.fragmentarium.infrastructure.queries import number_is, match_user_scopes
from ebl.fragmentarium.infrastructure.fragment_lemma_matcher import (
    LemmaMatcher,
    EmptyMatcher,
)
from ebl.common.query.query_result import LemmaQueryType
from ebl.fragmentarium.infrastructure.fragment_sign_matcher import SignMatcher

from pydash.arrays import compact


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
            else EmptyMatcher()
        )

        self._sign_matcher = (
            SignMatcher(query["transliteration"])
            if "transliteration" in query
            else EmptyMatcher()
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

    def _prefilter(self) -> List[Dict]:
        constraints = {
            "$and": compact(
                [
                    number_is(self._query["number"]) if "number" in self._query else {},
                    self._filter_by_genre(),
                    self._filter_by_project(),
                    self._filter_by_script(),
                    self._filter_by_reference(),
                    match_user_scopes(self._scopes),
                ]
            ),
        }

        return [{"$match": constraints}] if constraints else []

    def _default_pipeline(self) -> List[Dict]:
        return [
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

    def _get_pipeline_components(self) -> List[Dict]:
        dispatcher = {
            (True, True): self._merge_pipelines,
            (True, False): self._lemma_matcher.build_pipeline,
            (False, True): self._sign_matcher.build_pipeline,
            (False, False): self._default_pipeline,
        }
        key = (
            isinstance(self._lemma_matcher, LemmaMatcher),
            isinstance(self._sign_matcher, SignMatcher),
        )

        return [
            *self._prefilter(),
            *dispatcher[key](),
            *self._wrap_query_items_with_total(
                sort_fields={"script.sortKey": 1, "_sortKey": 1}
            ),
        ]

    def build_pipeline(self) -> List[Dict]:
        return self._get_pipeline_components()
