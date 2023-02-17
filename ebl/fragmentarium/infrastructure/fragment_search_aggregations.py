from typing import List, Dict, Sequence
from ebl.common.domain.scopes import Scope
from ebl.fragmentarium.infrastructure.queries import number_is, match_user_scopes
from ebl.fragmentarium.infrastructure.fragment_lemma_matcher import LemmaMatcher
from ebl.common.query.query_result import LemmaQueryType
from ebl.fragmentarium.infrastructure.fragment_sign_matcher import SignMatcher
from pydash.arrays import compact

VOCAB_PATH = "vocabulary"
LEMMA_PATH = "text.lines.content.uniqueLemma"


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

    def _wrap_query_items_with_total(self) -> List[Dict]:
        return [
            {"$sort": {"matchCount": -1, "_id": 1}},
            *self._limit_result(),
            {"$project": {"_id": False}},
            {
                "$group": {
                    "_id": None,
                    "items": {"$push": "$$ROOT"},
                    "matchCountTotal": {"$sum": "$matchCount"},
                }
            },
            {"$project": {"_id": False}},
        ]

    def _prefilter(self) -> List[Dict]:
        number_query = (
            number_is(self._query["number"]) if "number" in self._query else {}
        )
        id_query = (
            {"references": {"$elemMatch": {"id": self._query["bibId"]}}}
            if "bibId" in self._query
            else {}
        )
        if "pages" in self._query:
            id_query["references"]["$elemMatch"]["pages"] = {
                "$regex": rf".*?(^|[^\d]){self._query['pages']}([^\d]|$).*?"
            }
        constraints = {
            "$and": compact([number_query, match_user_scopes(self._scopes)]),
            **id_query,
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

    def build_pipeline(self) -> List[Dict]:
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
                            "matchingLines": {"$range": [0, {"$size": "$text.lines"}]},
                            "matchCount": {"$literal": 0},
                        }
                    },
                ]
            )

        pipeline.extend(self._wrap_query_items_with_total())

        return pipeline
