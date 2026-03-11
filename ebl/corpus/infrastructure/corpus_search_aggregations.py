from typing import Dict, List
from ebl.common.query.query_result import LemmaQueryType
from ebl.common.query.util import flatten_field
from ebl.corpus.infrastructure.corpus_lemma_matcher import CorpusLemmaMatcher
from ebl.corpus.infrastructure.corpus_sign_matcher import CorpusSignMatcher


class CorpusPatternMatcher:
    def __init__(self, query: Dict):
        self._query = query

        self._lemma_matcher = (
            CorpusLemmaMatcher(
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
            {"$sort": {"matchCount": -1, "textId": 1}},
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

    def _drop_merged_duplicates(self) -> List[Dict]:
        return [
            {
                "$project": {
                    "linesAndVariants": {"$zip": {"inputs": ["$lines", "$variants"]}}
                }
            },
            {"$unwind": "$linesAndVariants"},
            {
                "$project": {
                    "line": {"$first": "$linesAndVariants"},
                    "variant": {"$last": "$linesAndVariants"},
                }
            },
            {
                "$group": {
                    "_id": {
                        "stage": "$_id.stage",
                        "name": "$_id.name",
                        "textId": "$_id.textId",
                        "line": "$line",
                        "variant": "$variant",
                    }
                }
            },
            {"$replaceRoot": {"newRoot": "$_id"}},
            {"$sort": {"line": 1, "variant": 1}},
        ]

    def _merge_pipelines(self) -> List[Dict]:
        return [
            {
                "$facet": {
                    "lemmas": self._lemma_matcher.build_pipeline(
                        count_matches_per_item=False
                    ),
                    "signs": self._sign_matcher.build_pipeline(
                        count_matches_per_item=False
                    ),
                }
            },
            {"$project": {"combined": {"$concatArrays": ["$lemmas", "$signs"]}}},
            {"$unwind": "$combined"},
            {"$replaceRoot": {"newRoot": "$combined"}},
            {
                "$group": {
                    "_id": {"stage": "$stage", "name": "$name", "textId": "$textId"},
                    "lines": {"$push": "$lines"},
                    "variants": {"$push": "$variants"},
                }
            },
            {"$match": {"lines": {"$size": 2}}},
            {
                "$addFields": {
                    "lines": flatten_field("$lines"),
                    "variants": flatten_field("$variants"),
                }
            },
            *self._drop_merged_duplicates(),
            {"$sort": {"line": 1}},
            {
                "$group": {
                    "_id": {
                        "stage": "$stage",
                        "name": "$name",
                        "textId": "$textId",
                    },
                    "lines": {"$push": "$line"},
                    "variants": {"$push": "$variant"},
                }
            },
            {"$match": {"lines": {"$exists": True, "$not": {"$size": 0}}}},
            {"$addFields": {"matchCount": {"$size": "$lines"}}},
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

    def build_pipeline(self) -> List[Dict]:
        pipeline = []

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
