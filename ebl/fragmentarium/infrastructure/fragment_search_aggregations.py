from typing import List, Dict
from enum import Enum
from ebl.fragmentarium.infrastructure.queries import number_is


VOCAB_PATH = "vocabulary"
LEMMA_PATH = "text.lines.content.uniqueLemma"


class QueryType(Enum):
    AND = "and"
    OR = "or"
    LINE = "line"
    PHRASE = "phrase"
    LEMMA = "lemma"


class SignMatcher:
    def __init__(self, pattern: List[str]):
        self.pattern = pattern
        self._pattern_length = len(pattern)

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
                [
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
                if self._pattern_length == 1
                else self._match_transliteration_lines()
            ),
            {
                "$group": {
                    "_id": "$_id",
                    "museumNumber": {"$first": "$museumNumber"},
                    "matchingLines": {
                        "$push": {"$arrayElemAt": ["$textLines", "$chunkIndex"]}
                    },
                    **({"matchCount": {"$sum": 1}} if count_matches_per_item else {}),
                }
            },
        ]


class LemmaMatcher:
    unique_lemma_path = "text.lines.content.uniqueLemma"
    vocabulary_path = "vocabulary"
    flat_path = "lemmas"

    def __init__(
        self,
        pattern: List[str],
        query_type: QueryType,
    ):
        self.pattern = pattern
        self.query_type = query_type

    def build_pipeline(self, count_matches_per_item=True) -> List[Dict]:
        pipelines = {
            QueryType.LEMMA: self._lemma,
            QueryType.AND: self._and,
            QueryType.OR: self._or,
            QueryType.LINE: self._line,
            QueryType.PHRASE: self._phrase,
        }
        return pipelines[self.query_type](count_matches_per_item)

    def _flatten_lemmas(self) -> List[dict]:
        return [
            {
                "$addFields": {
                    self.vocabulary_path: {
                        "$setIntersection": {
                            "$reduce": {
                                "input": f"${self.flat_path}",
                                "initialValue": [],
                                "in": {"$concatArrays": ["$$value", "$$this"]},
                            }
                        }
                    },
                }
            }
        ]

    def _explode_lines(self) -> List[dict]:
        return [
            {
                "$project": {
                    "museumNumber": 1,
                    self.flat_path: f"${self.unique_lemma_path}",
                }
            },
            {
                "$unwind": {
                    "path": f"${self.flat_path}",
                    "includeArrayIndex": "lineIndex",
                }
            },
        ]

    def _rejoin_lines(self, count_matches_per_item=True) -> List[Dict]:
        return [
            {
                "$group": {
                    "_id": "$_id",
                    "matchingLines": {"$push": "$lineIndex"},
                    "museumNumber": {"$first": "$museumNumber"},
                    **({"matchCount": {"$sum": 1}} if count_matches_per_item else {}),
                }
            },
        ]

    def _create_match_pipeline(
        self, fragment_query: Dict, line_query: Dict, count_matches_per_item=True
    ) -> List[Dict]:
        return [
            {"$match": fragment_query},
            *self._explode_lines(),
            *self._flatten_lemmas(),
            {"$match": line_query},
            *self._rejoin_lines(count_matches_per_item),
        ]

    def _lemma(self, count_matches_per_item=True) -> List[Dict]:
        lemma = self.pattern[0]
        return self._create_match_pipeline(
            {self.unique_lemma_path: lemma},
            {self.vocabulary_path: lemma},
            count_matches_per_item,
        )

    def _and(self, count_matches_per_item=True) -> List[Dict]:
        return self._create_match_pipeline(
            {self.unique_lemma_path: {"$all": self.pattern}},
            {"$or": [{self.vocabulary_path: lemma} for lemma in self.pattern]},
            count_matches_per_item,
        )

    def _or(self, count_matches_per_item=True) -> List[Dict]:
        return self._create_match_pipeline(
            {self.unique_lemma_path: {"$in": self.pattern}},
            {self.vocabulary_path: {"$in": self.pattern}},
            count_matches_per_item,
        )

    def _line(self, count_matches_per_item=True) -> List[Dict]:
        return self._create_match_pipeline(
            {self.unique_lemma_path: {"$all": self.pattern}},
            {self.vocabulary_path: {"$all": self.pattern}},
            count_matches_per_item,
        )

    def _phrase(self, count_matches_per_item=True) -> List[Dict]:
        return [
            {"$match": {self.unique_lemma_path: {"$all": self.pattern}}},
            *self._explode_lines(),
            {"$match": {self.flat_path: {"$ne": [], "$exists": True}}},
            {
                "$project": {
                    "ngram": {
                        "$zip": {
                            "inputs": [
                                f"${self.flat_path}",
                                *(
                                    {
                                        "$slice": [
                                            f"${self.flat_path}",
                                            i + 1,
                                            {"$size": f"${self.flat_path}"},
                                        ]
                                    }
                                    for i in range(len(self.pattern) - 1)
                                ),
                            ]
                        }
                    },
                    "lineIndex": True,
                    "museumNumber": True,
                }
            },
            {"$addFields": {"ngram": {"$setUnion": ["$ngram", []]}}},
            {"$unwind": "$ngram"},
            {
                "$match": {
                    "$expr": {
                        "$and": [
                            {"$in": [lemma, {"$arrayElemAt": ["$ngram", i]}]}
                            for i, lemma in enumerate(self.pattern)
                        ]
                    }
                }
            },
            *self._rejoin_lines(),
        ]


class PatternMatcher:
    def __init__(self, query: Dict):
        self._query = query

        self._lemma_matcher = (
            LemmaMatcher(
                query["lemmas"],
                query.get("lemma-operator", QueryType.AND),
            )
            if "lemmas" in query
            else None
        )

        self._sign_matcher = (
            SignMatcher(query["transliteration"])
            if "transliteration" in query
            else None
        )

    def _wrap_query_items_with_total(self) -> List[Dict]:
        return [
            {"$sort": {"matchCount": -1}},
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
            {"references": {"$elemMatch": {"id": self._query["bibliographyId"]}}}
            if "bibliographyId" in self._query
            else {}
        )
        if "pages" in self._query:
            id_query["references"]["$elemMatch"]["pages"] = {
                "$regex": rf".*?(^|[^\d]){self._query['pages']}([^\d]|$).*?"
            }

        constraints = {**number_query, **id_query}

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
                "$addFields": {
                    "matchingLines": {
                        "$setIntersection": {
                            "$reduce": {
                                "input": "$matchingLines",
                                "initialValue": [],
                                "in": {"$concatArrays": ["$$value", "$$this"]},
                            }
                        }
                    }
                }
            },
            {"$addFields": {"matchCount": {"$size": "$matchingLines"}}},
        ]

    def build_pipeline(self) -> List[Dict]:
        pipeline = self._prefilter()

        if self._lemma_matcher and self._sign_matcher:
            pipeline.extend(self._merge_pipelines())
        elif self._lemma_matcher:
            pipeline.extend(self._lemma_matcher.build_pipeline())
        elif self._sign_matcher:
            pipeline.extend(self._sign_matcher.build_pipeline())

        pipeline.extend(self._wrap_query_items_with_total())

        return pipeline
