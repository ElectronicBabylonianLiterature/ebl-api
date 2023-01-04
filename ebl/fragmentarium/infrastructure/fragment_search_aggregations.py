from typing import Tuple, List, Dict, Sequence, Optional
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


class TransliterationMatcher:
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

    def build_pipeline(self) -> List[Dict]:
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
                    "matchCount": {"$sum": 1},
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
        count_matches_per_item=True,
    ):
        self.pattern = pattern
        self.query_type = query_type
        self._count_matches = count_matches_per_item

    def build_pipeline(self) -> List[Dict]:
        pipelines = {
            QueryType.LEMMA: self._lemma,
            QueryType.AND: self._and,
            QueryType.OR: self._or,
            QueryType.LINE: self._line,
            QueryType.PHRASE: self._phrase,
        }
        return pipelines[self.query_type]()

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

    def _rejoin_lines(self) -> List[Dict]:
        return [
            {
                "$group": {
                    "_id": "$_id",
                    "matchingLines": {"$push": "$lineIndex"},
                    "museumNumber": {"$first": "$museumNumber"},
                    **({"matchCount": {"$sum": 1}} if self._count_matches else {}),
                }
            },
        ]

    def _create_match_pipeline(
        self, fragment_query: Dict, line_query: Dict
    ) -> List[Dict]:
        return [
            {"$match": fragment_query},
            *self._explode_lines(),
            *self._flatten_lemmas(),
            {"$match": line_query},
            *self._rejoin_lines(),
        ]

    def _lemma(self) -> List[Dict]:
        lemma = self.pattern[0]
        return self._create_match_pipeline(
            {self.unique_lemma_path: lemma},
            {self.vocabulary_path: lemma},
        )

    def _and(self) -> List[Dict]:
        return self._create_match_pipeline(
            {self.unique_lemma_path: {"$all": self.pattern}},
            {"$or": [{self.vocabulary_path: lemma} for lemma in self.pattern]},
        )

    def _or(self) -> List[Dict]:
        return self._create_match_pipeline(
            {self.unique_lemma_path: {"$in": self.pattern}},
            {self.vocabulary_path: {"$in": self.pattern}},
        )

    def _line(self) -> List[Dict]:
        return self._create_match_pipeline(
            {self.unique_lemma_path: {"$all": self.pattern}},
            {self.vocabulary_path: {"$all": self.pattern}},
        )

    def _phrase(self) -> List[Dict]:
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
        self._lemmas: List[str] = query.get("lemmas")
        self._lemma_operator = query.get("lemma-operator")
        self._transliteration: List[str] = query.get("transliteration")

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
        number_query = number_is(self.query["number"]) if "number" in self.query else {}
        id_query = (
            {"references": {"$elemMatch": {"id": self.query["bibliographyId"]}}}
            if "bibliographyId" in self.query
            else {}
        )
        if "pages" in self.query:
            id_query["references"]["$elemMatch"]["pages"] = {
                "$regex": rf".*?(^|[^\d]){self.query['pages']}([^\d]|$).*?"
            }

        constraints = {**number_query, **id_query}

        return [{"$match": constraints}] if constraints else []

    def _match_merged(self) -> List[Dict]:
        return [
            {
                "$facet": {
                    "transliteration": self._match_transliteration(),
                    "lemmas": self._match_lemmas(),
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

    def build(self) -> List[Dict]:
        pipeline = self._prefilter()

        if self._lemmas and self._transliteration:
            pipeline.extend(self._match_merged())
        elif self._lemmas:
            pipeline.extend(self._match_lemmas())
        elif self._transliteration:
            pipeline.extend(self._match_transliteration())

        pipeline.extend(self._wrap_query_items_with_total())

        return pipeline


def _flatten_lemmas() -> List[dict]:
    return [
        {"$project": {"museumNumber": 1, "line": "$text.lines.content"}},
        {"$unwind": {"path": "$line", "includeArrayIndex": "lineIndex"}},
        {
            "$project": {
                "_id": 1,
                "lemmas": "$line.uniqueLemma",
                "lineIndex": 1,
                "tokenIndex": 1,
                "museumNumber": 1,
            }
        },
        {
            "$addFields": {
                VOCAB_PATH: {
                    "$setIntersection": {
                        "$reduce": {
                            "input": "$lemmas",
                            "initialValue": [],
                            "in": {"$concatArrays": ["$$value", "$$this"]},
                        }
                    }
                },
            }
        },
    ]


def _wrap_query_items_with_total() -> List[Dict]:
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


def _arrange_result(include_lemma_sequences=False) -> List[dict]:
    return [
        {
            "$group": {
                "_id": "$_id",
                "matchingLines": {"$push": "$lineIndex"},
                "museumNumber": {"$first": "$museumNumber"},
                **(
                    {"lemmaSequences": {"$push": "$lemmas"}}
                    if include_lemma_sequences
                    else {}
                ),
                "matchCount": {"$sum": 1},
            }
        },
        {"$sort": {"matchCount": -1}},
        {
            "$group": {
                "_id": None,
                **(
                    {}
                    if include_lemma_sequences
                    else {"matchCountTotal": {"$sum": "$matchCount"}}
                ),
                "items": {"$push": "$$ROOT"},
            }
        },
        {"$project": {"_id": 0}},
    ]


def _search_and_filter(
    line_matcher: dict, vocabulary_matcher: dict, include_lemma_sequences=False
) -> List[dict]:
    return [
        {"$match": line_matcher},
        *_flatten_lemmas(),
        {"$match": vocabulary_matcher},
        *_arrange_result(include_lemma_sequences),
    ]


def create_search_aggregation(
    query_operator: QueryType, lemmas: Sequence[str]
) -> List[dict]:
    matchers: Dict[QueryType, Tuple[dict, dict]] = {
        QueryType.LEMMA: (
            {LEMMA_PATH: lemmas[0]},
            {VOCAB_PATH: lemmas[0]},
        ),
        QueryType.AND: (
            {LEMMA_PATH: {"$all": lemmas}},
            {"$or": [{VOCAB_PATH: lemma} for lemma in lemmas]},
        ),
        QueryType.OR: (
            {"$or": [{LEMMA_PATH: lemma} for lemma in lemmas]},
            {"$or": [{VOCAB_PATH: lemma} for lemma in lemmas]},
        ),
        QueryType.LINE: (
            {LEMMA_PATH: {"$all": lemmas}},
            {VOCAB_PATH: {"$all": lemmas}},
        ),
        QueryType.PHRASE: (
            {LEMMA_PATH: {"$all": lemmas}},
            {VOCAB_PATH: {"$all": lemmas}},
        ),
    }

    return _search_and_filter(
        *matchers[query_operator],
        include_lemma_sequences=query_operator == QueryType.PHRASE,
    )


def lemma_pattern_match(pattern: List[str]) -> List[Dict]:

    pattern_length = len(pattern)

    return [
        {
            "$match": {
                "$and": [{"text.lines.content.uniqueLemma": lemma} for lemma in pattern]
            }
        },
        {
            "$project": {
                "lemmaSequence": "$text.lines.content.uniqueLemma",
                "museumNumber": True,
            }
        },
        {"$unwind": {"path": "$lemmaSequence", "includeArrayIndex": "lineIndex"}},
        {"$match": {"lemmaSequence": {"$ne": [], "$exists": True}}},
        {
            "$project": {
                "ngram": {
                    "$zip": {
                        "inputs": [
                            "$lemmaSequence",
                            *(
                                {
                                    "$slice": [
                                        "$lemmaSequence",
                                        i + 1,
                                        {"$size": "$lemmaSequence"},
                                    ]
                                }
                                for i in range(pattern_length - 1)
                            ),
                        ]
                    }
                },
                "lineIndex": True,
                "museumNumber": True,
            }
        },
        {"$addFields": {"ngram": {"$setUnion": ["$ngram", []]}}},
        {"$unwind": {"path": "$ngram", "includeArrayIndex": "ngramIndex"}},
        {
            "$match": {
                "$expr": {
                    "$and": [
                        {"$in": [lemma, {"$arrayElemAt": ["$ngram", i]}]}
                        for i, lemma in enumerate(pattern)
                    ]
                }
            }
        },
        {
            "$group": {
                "_id": "$_id",
                "lineIndex": {"$push": "$lineIndex"},
                "matchCount": {"$sum": 1},
                "museumNumber": {"$first": "$museumNumber"},
            }
        },
        *_wrap_query_items_with_total(),
    ]


def _match_transliteration_lines(line_patterns: List[str]) -> List[Dict]:
    pattern_length = len(line_patterns)
    return (
        [
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
                                    for i in range(pattern_length - 1)
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
                    for i, line_pattern in enumerate(line_patterns)
                }
            },
        ]
        if pattern_length > 1
        else [
            {"$unwind": {"path": "$signLines", "includeArrayIndex": "chunkIndex"}},
            {
                "$match": {
                    "signLines": {"$regex": line_patterns[0]},
                }
            },
        ]
    )


def match_transliteration(transliteration: Optional[List[str]]) -> List[Dict]:
    if not transliteration:
        return []

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
        *_match_transliteration_lines(transliteration),
        {
            "$group": {
                "_id": "$_id",
                "museumNumber": {"$first": "$museumNumber"},
                "matchingLines": {
                    "$push": {"$arrayElemAt": ["$textLines", "$chunkIndex"]}
                },
                "matchCount": {"$sum": 1},
            }
        },
    ]


def prefilter_fragments(query: Dict) -> List[Dict]:
    number_query = number_is(query["number"]) if "number" in query else {}
    id_query = (
        {"references": {"$elemMatch": {"id": query["bibliographyId"]}}}
        if "bibliographyId" in query
        else {}
    )
    if "pages" in query:
        id_query["references"]["$elemMatch"]["pages"] = {
            "$regex": rf".*?(^|[^\d]){query['pages']}([^\d]|$).*?"
        }

    # TODO: accession? CDLI? Script?
    constraints = {**number_query, **id_query}
    return [{"$match": constraints}] if constraints else []


def create_query_aggregation(query) -> List[Dict]:
    return [
        *prefilter_fragments(query),
        *match_transliteration(query.get("transliteration")),
        # TODO: match lemmas here
        *_wrap_query_items_with_total(),
    ]
