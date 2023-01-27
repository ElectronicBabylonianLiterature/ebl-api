from typing import Dict, List
from ebl.common.query.query_result import LemmaQueryType
from ebl.corpus.infrastructure.manuscript_lemma_matcher import ManuscriptLemmaMatcher
from ebl.corpus.infrastructure.reconstruction_lemma_matcher import (
    ReconstructionLemmaMatcher,
)
from ebl.corpus.infrastructure.sign_matcher import CorpusSignMatcher


class CorpusPatternMatcher:
    def __init__(self, query: Dict):
        self._query = query

        self._reconstruction_lemma_matcher = (
            ReconstructionLemmaMatcher(
                query["lemmas"],
                query.get("lemmaOperator", LemmaQueryType.AND),
            )
            if "lemmas" in query
            else None
        )
        self._manuscript_lemma_matcher = (
            ManuscriptLemmaMatcher(
                query["lemmas"],
                query.get("lemmaOperator", LemmaQueryType.AND),
            )
            if "lemmas" in query
            else None
        )
        self._sign_matcher = (
            CorpusSignMatcher(query["transliteration"])
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

    def _deduplicate_merged(self) -> List[Dict]:
        return [
            {
                "$addFields": {
                    "zipped": {
                        "$setUnion": [{"$zip": {"inputs": ["$lines", "$variants"]}}, []]
                    }
                }
            },
            {
                "$project": {
                    "lines": {
                        "$map": {
                            "input": "$zipped",
                            "as": "tuple",
                            "in": {"$arrayElemAt": ["$$tuple", 0]},
                        }
                    },
                    "variants": {
                        "$map": {
                            "input": "$zipped",
                            "as": "tuple",
                            "in": {"$arrayElemAt": ["$$tuple", 1]},
                        }
                    },
                }
            },
        ]

    def _merge_pipelines(self) -> List[Dict]:
        return [
            {
                "$facet": {
                    "reconstruction_lemmas": self._reconstruction_lemma_matcher.build_pipeline(
                        count_matches_per_item=False
                    ),
                    "manuscript_lemmas": self._manuscript_lemma_matcher.build_pipeline(
                        count_matches_per_item=False
                    ),
                }
            },
            {
                "$project": {
                    "combined": {
                        "$concatArrays": [
                            "$reconstruction_lemmas",
                            "$manuscript_lemmas",
                        ]
                    }
                }
            },
            {"$unwind": "$combined"},
            {"$replaceRoot": {"newRoot": "$combined"}},
            {
                "$group": {
                    "_id": {"stage": "$stage", "name": "$name", "textId": "$textId"},
                    "lines": {"$push": "$lines"},
                    "variants": {"$push": "$variants"},
                },
            },
            {
                "$match": {
                    "lines": {"$size": 2},
                }
            },
            {
                "$addFields": {
                    "lines": {
                        "$concatArrays": [
                            {"$arrayElemAt": ["$lines", 0]},
                            {"$arrayElemAt": ["$lines", 1]},
                        ]
                    },
                    "variants": {
                        "$concatArrays": [
                            {"$arrayElemAt": ["$variants", 0]},
                            {"$arrayElemAt": ["$variants", 1]},
                        ]
                    },
                }
            },
            *self._deduplicate_merged(),
            {"$addFields": {"matchCount": {"$size": "$lines"}}},
            {"$match": {"matchCount": {"$gt": 0}}},
            {
                "$project": {
                    "_id": False,
                    "stage": "$_id.stage",
                    "name": "$_id.name",
                    "textId": "$_id.textId",
                    "lines": True,
                    "variants": True,
                    "matchCount": True,
                }
            },
        ]

    def build_pipeline(
        self, include_reconstruction=True, include_manuscripts=True
    ) -> List[Dict]:
        pipeline = []

        if all(
            [
                self._reconstruction_lemma_matcher,
                self._manuscript_lemma_matcher,
                include_reconstruction,
                include_manuscripts,
            ]
        ):
            pipeline.extend(self._merge_pipelines())
        elif self._reconstruction_lemma_matcher and include_reconstruction:
            pipeline.extend(self._reconstruction_lemma_matcher.build_pipeline())
        elif self._manuscript_lemma_matcher and include_manuscripts:
            pipeline.extend(self._manuscript_lemma_matcher.build_pipeline())
        else:
            pipeline.extend(
                [
                    {
                        "$project": {
                            "textId": True,
                            "stage": True,
                            "name": True,
                            "lines": [],
                            "variants": [],
                            "matchCount": {"$literal": 0},
                        }
                    },
                ]
            )

        pipeline.extend(self._wrap_query_items_with_total())

        return pipeline
