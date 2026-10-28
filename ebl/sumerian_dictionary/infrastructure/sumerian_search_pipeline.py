import re
from typing import List, Mapping, Sequence

from ebl.common.query.query_collation import CollatedFieldQuery, DataType, Fields
from ebl.sumerian_dictionary.domain.search_query import (
    PROPER_NOUN_TAGS,
    Kind,
    SourceFilter,
    SumerianWordQuery,
)

DATA_TYPE: DataType = "sumerian-dictionary"
ENGLISH_SENSE_LIMIT = 4
OPTIONAL_BRACES = "[{}]*"
IS_OBJECT = {"$type": "object"}
MANAGED_DOCUMENT = {"sources": IS_OBJECT}
SEARCHED_FIELDS: Sequence[str] = Fields.SUMERIAN_DICTIONARY.value["COLLATED_FIELDS"]
PROPER_NOUNS = sorted(PROPER_NOUN_TAGS)


def _as_array(path: str) -> dict:
    return {"$cond": [{"$isArray": f"${path}"}, f"${path}", []]}


def _size(path: str) -> dict:
    return {"$size": _as_array(path)}


def _values(path: str) -> dict:
    return {"$ifNull": [f"${path}", []]}


def _has_object(path: str) -> dict:
    return {"$eq": [{"$type": f"${path}"}, "object"]}


def _first_cuneiform(*conditions: dict) -> dict:
    complete_matches = {
        "$filter": {
            "input": _as_array("renderings"),
            "cond": {"$and": [{"$eq": ["$$this.complete", True]}, *conditions]},
        }
    }
    first_sequences = {
        "$map": {
            "input": complete_matches,
            "in": {"$arrayElemAt": ["$$this.cuneiform", 0]},
        }
    }
    return {"$arrayElemAt": [first_sequences, 0]}


def _head_cuneiform() -> dict:
    key = _first_cuneiform({"$eq": ["$$this.kind", "key"]})
    citation_form = _first_cuneiform(
        {"$eq": ["$$this.source", "epsd2"]},
        {"$eq": ["$$this.spelling", "$citationForm"]},
    )
    return {"$ifNull": [key, {"$ifNull": [citation_form, ""]}]}


def summary_projection() -> dict:
    return {
        "citationForm": 1,
        "homonym": 1,
        "guideWord": 1,
        "pos": 1,
        "attingerPos": 1,
        "language": 1,
        "cuneiform": _head_cuneiform(),
        "frenchSenses": _values("attingerSenses.meaning"),
        "englishSenses": {
            "$slice": [_values("epsd2Senses.meaning"), ENGLISH_SENSE_LIMIT]
        },
        "hasAttinger": _has_object("sources.attinger"),
        "hasEpsd2": _has_object("sources.epsd2"),
        "epsd2FormCount": _size("epsd2Forms"),
        "akkadianCount": _size("akkadianEquivalents"),
        "citationCount": _size("citations"),
        "compoundCount": {"$add": [_size("compounds"), _size("nameCompounds")]},
        "crossReferenceCount": _size("crossReferences"),
        "hasEmesal": {"$gt": [_size("emesal"), 0]},
        "attestationCount": {"$ifNull": ["$attestation.count", 0]},
    }


def search_projection() -> dict:
    return {
        **summary_projection(),
        "aliasForms": _values("aliases.form"),
        "senseMeanings": {
            "$concatArrays": [
                _values("attingerSenses.meaning"),
                _values("epsd2Senses.meaning"),
            ]
        },
        "akkadianWordIds": _values("akkadianEquivalents.wordId"),
    }


def _character_pattern(character: str) -> str:
    collated = CollatedFieldQuery(character, SEARCHED_FIELDS[0], DATA_TYPE).value
    return collated or re.escape(character)


def brace_tolerant_pattern(folded_query: str) -> str:
    return OPTIONAL_BRACES.join(
        _character_pattern(character) for character in folded_query
    )


def _kind_filter(kind: Kind) -> List[dict]:
    if kind == Kind.WORDS:
        return [{"pos": {"$nin": PROPER_NOUNS}}]
    if kind == Kind.NAMES:
        return [{"pos": {"$in": PROPER_NOUNS}}]
    return []


def _source_filter(source: SourceFilter) -> List[dict]:
    if source == SourceFilter.ANY:
        return []
    return [{f"sources.{source.value}": IS_OBJECT}]


def search_match(query: SumerianWordQuery, folded_query: str) -> dict:
    condition = {"$regex": brace_tolerant_pattern(folded_query), "$options": "i"}
    return {
        "$and": [
            MANAGED_DOCUMENT,
            {"$or": [{field: condition} for field in SEARCHED_FIELDS]},
            *_kind_filter(query.kind),
            *_source_filter(query.source),
        ]
    }


STATISTICS_FILTERS: Mapping[str, dict] = {
    "lemmas": {},
    "attinger": {"sources.attinger": IS_OBJECT},
    "aligned": {"sources.attinger": IS_OBJECT, "sources.epsd2": IS_OBJECT},
    "epsd2Only": {"sources.epsd2": IS_OBJECT, "sources.attinger": {"$not": IS_OBJECT}},
    "properNouns": {"pos": {"$in": PROPER_NOUNS}},
    "withAkkadian": {"akkadianEquivalents.0": {"$exists": True}},
}


def statistics_pipeline() -> List[dict]:
    return [
        {"$match": MANAGED_DOCUMENT},
        {
            "$facet": {
                name: [{"$match": condition}, {"$count": "count"}]
                for name, condition in STATISTICS_FILTERS.items()
            }
        },
    ]


def statistics_counts(facets: Mapping[str, Sequence[Mapping[str, int]]]) -> dict:
    return {
        name: facets[name][0]["count"] if facets[name] else 0
        for name in STATISTICS_FILTERS
    }
