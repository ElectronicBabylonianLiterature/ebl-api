from typing import Any, Dict, Optional, Sequence

from ebl.bibliography.application.bibliography_repository import BibliographyRepository
from ebl.bibliography.application.duplicate_audit import (
    PROJECTION,
    extract_year,
    normalize_doi,
    normalize_identifier,
)
from ebl.bibliography.application.serialization import (
    create_mongo_entry,
    create_object_entry,
)
from ebl.mongo_collection import MongoCollection

COLLECTION = "bibliography"


def join_reference_documents() -> Sequence[dict]:
    return [
        {"$unwind": {"path": "$references", "preserveNullAndEmptyArrays": True}},
        {
            "$lookup": {
                "from": "bibliography",
                "localField": "references.id",
                "foreignField": "_id",
                "as": "references.document",
            }
        },
        {
            "$set": {
                "references.document": {"$arrayElemAt": ["$references.document", 0]}
            }
        },
        {
            "$group": {
                "_id": "$_id",
                "references": {"$push": "$references"},
                "root": {"$first": "$$ROOT"},
            }
        },
        {
            "$replaceRoot": {
                "newRoot": {"$mergeObjects": ["$root", {"references": "$references"}]}
            }
        },
        {
            "$set": {
                "references": {
                    "$filter": {
                        "input": "$references",
                        "as": "reference",
                        "cond": {"$ne": ["$$reference", {}]},
                    }
                }
            }
        },
    ]


class MongoBibliographyRepository(BibliographyRepository):
    def __init__(self, database):
        self._collection = MongoCollection(database, COLLECTION)

    def create(self, entry) -> str:
        mongo_entry = create_mongo_entry(entry)
        return self._collection.insert_one(mongo_entry)

    def query_by_id(self, id_: str) -> dict:
        data = self._collection.find_one_by_id(id_)
        return create_object_entry(data)

    def query_by_ids(self, ids: Sequence[str]) -> Sequence[dict]:
        data = self._collection.find_many({"_id": {"$in": ids}})
        return [create_object_entry(item) for item in data]

    def update(self, entry) -> None:
        mongo_entry = create_mongo_entry(entry)
        self._collection.replace_one(mongo_entry)

    def query_by_author_year_and_title(
        self, author: Optional[str], year: Optional[int], title: Optional[str]
    ) -> Sequence[dict]:
        match: Dict[str, Any] = {}

        def pad_trailing_zeroes(year: int) -> int:
            padded_year = str(year).ljust(4, "0")
            return int(padded_year)

        if author:
            match["author.0.family"] = author
        if year:
            match["issued.date-parts.0.0"] = {
                "$gte": pad_trailing_zeroes(year),
                "$lt": pad_trailing_zeroes(year + 1),
            }
        if title:
            match["$expr"] = {"$eq": [{"$substrCP": ["$title", 0, len(title)]}, title]}
        return [
            create_object_entry(data)
            for data in self._collection.aggregate(
                [
                    {"$match": match},
                    {
                        "$addFields": {
                            "primaryYear": {
                                "$arrayElemAt": [
                                    {"$arrayElemAt": ["$issued.date-parts", 0]},
                                    0,
                                ]
                            }
                        }
                    },
                    {"$sort": {"author.0.family": 1, "primaryYear": 1, "title": 1}},
                    {"$project": {"primaryYear": 0}},
                ],
                collation={"locale": "en", "strength": 1, "normalization": True},
            )
        ]

    def query_by_container_title_and_collection_number(
        self, container_title_short: Optional[str], collection_number: Optional[str]
    ) -> Sequence[dict]:
        match: Dict[str, Any] = {}
        if container_title_short:
            match["container-title-short"] = container_title_short
        if collection_number:
            match["collection-number"] = collection_number
        return self._query(match)

    def query_by_title_short_and_volume(
        self, title_short: Optional[str], volume: Optional[str]
    ) -> Sequence[dict]:
        match: Dict[str, Any] = {}
        if title_short:
            match["title-short"] = title_short
        if volume:
            match["volume"] = volume
        return self._query(match)

    def query_duplicate_candidates(self, entry: Any, limit: int) -> Sequence[Any]:
        candidates: dict[str, dict] = {}
        for query in duplicate_candidate_queries(entry):
            for data in self._collection.find_many(query, projection=PROJECTION).limit(
                limit
            ):
                candidates[data["_id"]] = create_object_entry(data)
                if len(candidates) >= limit:
                    return list(candidates.values())
        return list(candidates.values())

    def _query(self, match: Dict[str, Any]) -> Sequence[dict]:
        return [
            create_object_entry(data)
            for data in self._collection.aggregate(
                [
                    {"$match": match},
                    {
                        "$addFields": {
                            "primaryYear": {
                                "$arrayElemAt": [
                                    {"$arrayElemAt": ["$issued.date-parts", 0]},
                                    0,
                                ]
                            }
                        }
                    },
                    {
                        "$sort": {
                            "author.0.family": 1,
                            "primaryYear": 1,
                            "collection-title": 1,
                        }
                    },
                    {"$project": {"primaryYear": 0}},
                ],
                collation={"locale": "en", "strength": 1, "normalization": True},
            )
        ]

    def list_all_bibliography(self) -> Sequence[str]:
        return self._collection.get_all_values("_id")


def duplicate_candidate_queries(entry: dict) -> Sequence[dict]:
    queries = []
    identifier_query = duplicate_identifier_query(entry)
    if identifier_query:
        queries.append(identifier_query)
    if author_year_query := contributor_year_query(entry):
        queries.append(author_year_query)
    if title_year_query := year_title_query(entry):
        queries.append(title_year_query)
    if container_query := container_title_year_query(entry):
        queries.append(container_query)
    if series_query := series_query_from_entry(entry):
        queries.append(series_query)
    return queries


def duplicate_identifier_query(entry: dict) -> Optional[dict]:
    clauses = []
    if doi_values := doi_variants(entry.get("DOI")):
        clauses.append({"DOI": {"$in": doi_values}})
    if isbn_values := identifier_variants(entry.get("ISBN")):
        clauses.append({"ISBN": {"$in": isbn_values}})
    if issn_values := identifier_variants(entry.get("ISSN")):
        clauses.append({"ISSN": {"$in": issn_values}})
    return {"$or": clauses} if clauses else None


def doi_variants(value: Any) -> Sequence[str]:
    normalized = normalize_doi(value)
    if not normalized:
        return []
    return sorted(
        {
            str(value).strip(),
            normalized,
            f"doi:{normalized}",
            f"doi: {normalized}",
            f"https://doi.org/{normalized}",
            f"http://doi.org/{normalized}",
            f"https://dx.doi.org/{normalized}",
            f"http://dx.doi.org/{normalized}",
        }
    )


def identifier_variants(value: Any) -> Sequence[str]:
    normalized = normalize_identifier(value)
    if not normalized:
        return []
    return sorted({str(value).strip(), normalized})


def contributor_year_query(entry: dict) -> Optional[dict]:
    family = first_contributor_family(entry)
    year = extract_year(entry)
    if family and year is not None:
        return {
            "$or": [{"author.0.family": family}, {"editor.0.family": family}],
            "issued.date-parts.0.0": year_range(year),
        }
    return None


def year_title_query(entry: dict) -> Optional[dict]:
    year = extract_year(entry)
    title = entry.get("title")
    if isinstance(title, str) and title and year is not None:
        return {"title": title, "issued.date-parts.0.0": year_range(year)}
    return None


def container_title_year_query(entry: dict) -> Optional[dict]:
    year = extract_year(entry)
    container_title = entry.get("container-title")
    if isinstance(container_title, str) and container_title and year is not None:
        query: dict[str, Any] = {
            "container-title": container_title,
            "issued.date-parts.0.0": year_range(year),
        }
        if entry.get("page"):
            query["page"] = entry["page"]
        return query
    return None


def series_query_from_entry(entry: dict) -> Optional[dict]:
    if entry.get("container-title-short") and entry.get("collection-number"):
        return {
            "container-title-short": entry["container-title-short"],
            "collection-number": entry["collection-number"],
        }
    if entry.get("title-short") and entry.get("volume"):
        return {"title-short": entry["title-short"], "volume": entry["volume"]}
    return None


def first_contributor_family(entry: dict) -> Optional[str]:
    people = entry.get("author") or entry.get("editor") or []
    if people and isinstance(people[0], dict):
        family = people[0].get("family")
        return family if isinstance(family, str) and family else None
    return None


def year_range(year: int) -> dict[str, int]:
    return {"$gte": pad_trailing_zeroes(year), "$lt": pad_trailing_zeroes(year + 1)}


def pad_trailing_zeroes(year: int) -> int:
    return int(str(year).ljust(4, "0"))
