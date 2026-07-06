from typing import Any, Dict, Iterator, List, Optional, Sequence, Union

from marshmallow import EXCLUDE
from pymongo.collation import Collation

from ebl.common.domain.scopes import Scope
from ebl.common.query.query_result import QueryResult, AfORegisterToFragmentQueryResult
from ebl.common.query.query_schemas import (
    QueryResultSchema,
    AfORegisterToFragmentQueryResultSchema,
)
from ebl.errors import NotFoundError
from ebl.fragmentarium.application.fragment_query_summary_schema import (
    FragmentQueryResultSchema,
)
from ebl.fragmentarium.domain.archaeology import ExcavationNumber
from ebl.fragmentarium.domain.fragment_query_summary import FragmentQueryResult
from ebl.fragmentarium.infrastructure.mongo_fragment_repository_base import (
    MongoFragmentRepositoryBase,
)
from ebl.transliteration.application.museum_number_schema import MuseumNumberSchema
from ebl.fragmentarium.domain.fragment_pager_info import FragmentPagerInfo
from ebl.fragmentarium.infrastructure.fragment_pattern_matcher import PatternMatcher
from ebl.fragmentarium.infrastructure.queries import (
    HAS_TRANSLITERATION,
    aggregate_latest,
    join_joins,
    join_findspots,
    aggregate_by_traditional_references,
)
from ebl.fragmentarium.infrastructure.queries import match_user_scopes
from ebl.transliteration.domain.museum_number import MuseumNumber
from ebl.transliteration.infrastructure.queries import query_number_is
from ebl.bibliography.infrastructure.bibliography import join_reference_documents
from ebl.fragmentarium.infrastructure.mongo_fragment_repository_get_extended import (
    MongoFragmentRepositoryGetExtended,
)
from ebl.transliteration.domain.atf import DEFAULT_ATF_PARSER_VERSION


RETRIEVE_ALL_LIMIT = 1000
FRAGMENT_QUERY_SUMMARY_PROJECTION = {
    "_id": True,
    "accession": True,
    "archaeology.excavationNumber": True,
    "archaeology.site": True,
    "date": True,
    "description": True,
    "dossiers": True,
    "genres": True,
    "museumNumber": True,
    "projects": True,
    "references": True,
    "script": True,
    "text.lines": True,
    "text.parser_version": True,
}


def load_museum_number(data: dict) -> MuseumNumber:
    return MuseumNumberSchema().load(data.get("museumNumber", data))


def load_query_result(cursor: Iterator) -> QueryResult:
    data = next(cursor, None)
    return QueryResultSchema().load(data) if data else QueryResult.create_empty()


def fragment_photo_filename(museum_number: Union[dict, MuseumNumber]) -> str:
    if isinstance(museum_number, MuseumNumber):
        return f"{museum_number}.jpg"

    suffix = museum_number.get("suffix") or ""
    suffix_part = f".{suffix}" if suffix else ""
    return f"{museum_number.get('prefix', '')}.{museum_number.get('number', '')}{suffix_part}.jpg"


def compact_preview_token(token: dict) -> dict:
    data = {
        "value": token.get("value"),
        "cleanValue": token.get("cleanValue"),
        "uniqueLemma": token.get("uniqueLemma"),
        "type": token.get("type"),
    }
    return {
        key: value
        for key, value in data.items()
        if value is not None and (key != "uniqueLemma" or value)
    }


def compact_preview_line(line: dict) -> dict:
    content = line.get("content") or []
    prefix = line.get("prefix") or ""
    return {
        "number": prefix,
        "prefix": prefix,
        "text": " ".join(token.get("value", "") for token in content),
        "tokens": [compact_preview_token(token) for token in content],
    }


def chapter_lemma_pipeline(clean_values: List[str]) -> List[dict]:
    return [
        {
            "$project": {
                "_id": 1,
                "lines.variants.reconstruction": {
                    "cleanValue": 1,
                    "uniqueLemma": 1,
                },
                "lines.variants.manuscripts.line.content": {
                    "cleanValue": 1,
                    "uniqueLemma": 1,
                },
            }
        },
        {"$unwind": "$lines"},
        {"$unwind": "$lines.variants"},
        {
            "$project": {
                "reconstruction": "$lines.variants.reconstruction",
                "manuscripts": "$lines.variants.manuscripts",
            }
        },
        {
            "$facet": {
                "reconstructionLemmas": [
                    {"$project": {"_id": False, "reconstruction": True}},
                    {"$unwind": "$reconstruction"},
                    {"$replaceRoot": {"newRoot": "$reconstruction"}},
                    {
                        "$match": {
                            "uniqueLemma.0": {"$exists": True},
                            "cleanValue": {"$in": clean_values},
                        }
                    },
                ],
                "manuscriptLemmas": [
                    {"$project": {"_id": False, "manuscripts": True}},
                    {"$unwind": "$manuscripts"},
                    {"$unwind": "$manuscripts.line.content"},
                    {"$replaceRoot": {"newRoot": "$manuscripts.line.content"}},
                    {
                        "$match": {
                            "uniqueLemma.0": {"$exists": True},
                            "cleanValue": {"$in": clean_values},
                        }
                    },
                ],
            }
        },
        {
            "$project": {
                "combinedLemmas": {
                    "$concatArrays": ["$reconstructionLemmas", "$manuscriptLemmas"]
                }
            }
        },
        {"$unwind": "$combinedLemmas"},
        {"$replaceRoot": {"newRoot": "$combinedLemmas"}},
    ]


def fragment_lemma_pipeline(clean_values: List[str]) -> List[dict]:
    return [
        {
            "$match": {
                "text.lines.content": {
                    "$elemMatch": {
                        "cleanValue": {"$in": clean_values},
                        "uniqueLemma.0": {"$exists": True},
                    }
                }
            }
        },
        {"$project": {"_id": False, "text.lines": True}},
        {"$unwind": "$text.lines"},
        {"$project": {"tokens": "$text.lines.content"}},
        {"$unwind": "$tokens"},
        {
            "$project": {
                "cleanValue": "$tokens.cleanValue",
                "uniqueLemma": "$tokens.uniqueLemma",
            }
        },
        {
            "$match": {
                "uniqueLemma.0": {"$exists": True},
                "cleanValue": {"$in": clean_values},
            }
        },
    ]


def aggregate_counts() -> List[dict]:
    return [
        {
            "$group": {
                "_id": {"cleanValue": "$cleanValue", "uniqueLemma": "$uniqueLemma"},
                "count": {"$sum": 1},
            }
        },
        {
            "$project": {
                "_id": 0,
                "cleanValue": "$_id.cleanValue",
                "uniqueLemma": "$_id.uniqueLemma",
                "count": True,
            }
        },
        {"$sort": {"count": -1}},
        {
            "$group": {
                "_id": "$cleanValue",
                "lemmatizations": {
                    "$addToSet": {"uniqueLemma": "$uniqueLemma", "count": "$count"}
                },
            }
        },
    ]


class MongoFragmentRepositoryGetBase(MongoFragmentRepositoryBase):
    def _omit_text_lines(self) -> List:
        return [{"$addFields": {"text.lines": []}}]

    def _filter_fragment_lines(self, lines: Optional[Sequence[int]]) -> List:
        return (
            [
                {
                    "$addFields": {
                        "text.lines": (
                            {
                                "$map": {
                                    "input": lines,
                                    "as": "i",
                                    "in": {"$arrayElemAt": ["$text.lines", "$$i"]},
                                }
                            }
                        )
                    }
                }
            ]
            if lines
            else []
        )

    def _find_fragment_query_summary_data(
        self, fragment_ids: Sequence[Any]
    ) -> Dict[Any, dict]:
        return {
            fragment["_id"]: fragment
            for fragment in self._fragments.find_many(
                {"_id": {"$in": list(fragment_ids)}},
                projection=FRAGMENT_QUERY_SUMMARY_PROJECTION,
            )
        }

    def _find_fragment_query_photo_filenames(
        self, items: Sequence[dict]
    ) -> Sequence[str]:
        filenames = [
            fragment_photo_filename(item["museumNumber"])
            for item in items
            if item.get("museumNumber")
        ]
        return [
            photo["filename"]
            for photo in self._photo_files.find_many(
                {"filename": {"$in": filenames}},
                projection={"filename": True},
            )
        ]

    def _matching_line_preview(self, fragment: dict, matching_lines: Sequence[int]):
        text = fragment.get("text") or {}
        lines = text.get("lines") or []
        return {
            "lines": [
                compact_preview_line(lines[line_index])
                for line_index in matching_lines
                if 0 <= line_index < len(lines)
            ],
            "parserVersion": text.get("parser_version") or DEFAULT_ATF_PARSER_VERSION,
        }

    def _hydrate_fragment_query_item(
        self,
        item: dict,
        fragments_by_id: Dict[Any, dict],
        photo_filenames: Sequence[str],
    ) -> dict:
        fragment = fragments_by_id.get(item["_id"])
        if fragment is None:
            raise NotFoundError(
                f"Fragment summary data for {item.get('museumNumber')} not found."
            )

        matching_lines = item.get("matchingLines") or []
        museum_number = fragment.get("museumNumber", item.get("museumNumber"))
        return {
            "museumNumber": museum_number,
            "accession": fragment.get("accession"),
            "description": fragment.get("description", ""),
            "script": fragment.get(
                "script",
                {"period": "", "periodModifier": "None", "uncertain": False},
            ),
            "date": fragment.get("date"),
            "genres": fragment.get("genres", []),
            "archaeology": fragment.get("archaeology"),
            "references": fragment.get("references", []),
            "projects": fragment.get("projects", []),
            "dossiers": fragment.get("dossiers", []),
            "matchingLines": matching_lines,
            "matchingLinePreview": self._matching_line_preview(
                fragment, matching_lines
            ),
            "matchCount": item.get("matchCount", 0),
            "hasPhoto": fragment_photo_filename(museum_number) in photo_filenames,
        }

    def _load_fragment_query_result(self, data: Optional[dict]) -> FragmentQueryResult:
        if not data:
            return FragmentQueryResult.create_empty()

        items = data.get("items", [])
        fragment_ids = [item["_id"] for item in items]
        fragments_by_id = self._find_fragment_query_summary_data(fragment_ids)
        photo_filenames = self._find_fragment_query_photo_filenames(items)
        return FragmentQueryResultSchema().load(
            {
                "items": [
                    self._hydrate_fragment_query_item(
                        item, fragments_by_id, photo_filenames
                    )
                    for item in items
                ],
                "matchCountTotal": data.get("matchCountTotal", 0),
                "isMatchCountTotalExact": data.get("isMatchCountTotalExact", True),
                "hasNextPage": data.get("hasNextPage"),
            }
        )

    def query_by_museum_number(
        self,
        number: Union[MuseumNumber, ExcavationNumber],
        lines: Optional[Sequence[int]] = None,
        exclude_lines=False,
    ):
        data = self._fragments.aggregate(
            [
                {"$match": query_number_is(number)},
                *(
                    self._omit_text_lines()
                    if exclude_lines
                    else self._filter_fragment_lines(lines)
                ),
                *join_findspots(),
                *join_reference_documents(),
                *join_joins(),
            ]
        )
        try:
            fragment_data = next(data)
            return self._schema(unknown=EXCLUDE).load(fragment_data)
        except StopIteration as error:
            raise NotFoundError(f"Fragment {number} not found.") from error

    def query_museum_numbers(self, prefix: str, number_regex: str) -> Sequence[dict]:
        return self._fragments.find_many(
            {
                "museumNumber.prefix": prefix,
                "museumNumber.number": {"$regex": number_regex},
            },
            projection={"museumNumber": True},
        )

    def query_by_sort_key(self, key: int) -> MuseumNumber:
        if key < 0:
            last_fragment = next(
                self._fragments.find_many(
                    {}, projection={"_sortKey": True, "museumNumber": True}
                )
                .sort("_sortKey", -1)
                .limit(1)
            )
            return load_museum_number(last_fragment)

        if match := next(
            self._fragments.aggregate(
                [
                    {"$match": {"_sortKey": {"$in": [0, key]}}},
                    {"$limit": 2},
                    {"$sort": {"_sortKey": -1}},
                    {"$project": {"museumNumber": True}},
                ]
            ),
            None,
        ):
            return load_museum_number(match)
        else:
            raise NotFoundError(f"Unable to find fragment with _sortKey {key}")

    def query_next_and_previous_fragment(
        self, museum_number: MuseumNumber
    ) -> FragmentPagerInfo:
        current = self._fragments.find_one(
            {
                "museumNumber.prefix": museum_number.prefix,
                "museumNumber.number": museum_number.number,
                "museumNumber.suffix": museum_number.suffix,
            },
            projection={"_sortKey": True},
        ).get("_sortKey")

        if current is None:
            prev = next_ = museum_number
        else:
            prev = self.query_by_sort_key(current - 1)
            next_ = self.query_by_sort_key(current + 1)

        return FragmentPagerInfo(prev, next_)

    def query(
        self, query: dict, user_scopes: Sequence[Scope] = ()
    ) -> Union[QueryResult, FragmentQueryResult]:
        cursor = (
            self._fragments.aggregate(
                PatternMatcher(
                    query, self._provenance_service, user_scopes
                ).build_pipeline(),
                collation=Collation(
                    locale="en", numericOrdering=True, alternate="shifted"
                ),
                allowDiskUse=True,
            )
            if set(query) - {"lemmaOperator"}
            else iter([])
        )
        return (
            self._load_fragment_query_result(next(cursor, None))
            if "limit" in query
            else load_query_result(cursor)
        )

    def query_latest(self) -> QueryResult:
        return load_query_result(
            self._fragments.aggregate(
                aggregate_latest(),
                collation=Collation(
                    locale="en", numericOrdering=True, alternate="shifted"
                ),
            )
        )

    def query_by_traditional_references(
        self,
        traditional_references: Sequence[str],
        user_scopes: Sequence[Scope] = (),
    ) -> AfORegisterToFragmentQueryResult:
        pipeline = aggregate_by_traditional_references(
            traditional_references, user_scopes
        )
        data = self._fragments.aggregate(pipeline)
        return (
            AfORegisterToFragmentQueryResultSchema().load({"items": data})
            if data
            else AfORegisterToFragmentQueryResult.create_empty()
        )

    def list_all_fragments(self, user_scopes: Sequence[Scope] = ()) -> Sequence[str]:
        return list(
            self._fragments.get_all_values("_id", match_user_scopes(user_scopes))
        )

    def retrieve_transliterated_fragments(self, skip: int) -> Sequence[dict]:
        fragments = self._fragments.aggregate(
            [
                {
                    "$match": HAS_TRANSLITERATION
                    | {"authorizedScopes": {"$exists": False}}
                },
                {
                    "$project": {
                        "folios": 0,
                        "lineToVec": 0,
                        "authorizedScops": 0,
                        "references": 0,
                        "uncuratedReferences": 0,
                        "genreLegacy": 0,
                        "legacyJoins": 0,
                        "legacyScript": 0,
                        "_sortKey": 0,
                    }
                },
                {"$skip": skip},
                {"$limit": RETRIEVE_ALL_LIMIT},
            ]
        )
        return list(fragments)

    def collect_lemmas(self, number: MuseumNumber):
        fragment = self.query_by_museum_number(number)
        clean_values = list(
            {
                token.clean_value
                for line in fragment.text.text_lines
                for token in line.content
                if token.lemmatizable
            }
        )
        return {
            element["_id"]: max(
                element["lemmatizations"], key=lambda entry: entry["count"]
            )["uniqueLemma"]
            for element in self._fragments.aggregate(
                [
                    *fragment_lemma_pipeline(clean_values),
                    {
                        "$unionWith": {
                            "coll": "chapters",
                            "pipeline": chapter_lemma_pipeline(clean_values),
                        }
                    },
                    *aggregate_counts(),
                ]
            )
        }


class MongoFragmentRepositoryGet(
    MongoFragmentRepositoryGetBase, MongoFragmentRepositoryGetExtended
):
    pass
