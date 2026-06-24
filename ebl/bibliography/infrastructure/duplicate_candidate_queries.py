from __future__ import annotations

import re
from typing import Any, Optional, Sequence

from ebl.bibliography.application.duplicate_audit import (
    extract_year,
    normalize_doi,
    normalize_identifier,
)


def duplicate_candidate_queries(entry: dict) -> Sequence[dict]:
    queries = []
    queries.extend(duplicate_strong_identifier_queries(entry))
    if author_year_query := contributor_year_query(entry):
        queries.append(author_year_query)
    if title_year_query := year_title_query(entry):
        queries.append(title_year_query)
    if container_query := container_title_year_query(entry):
        queries.append(container_query)
    if series_query := series_query_from_entry(entry):
        queries.append(series_query)
    queries.extend(duplicate_supporting_identifier_queries(entry))
    return queries


def duplicate_strong_identifier_queries(entry: dict) -> Sequence[dict]:
    queries = []
    if doi_values := doi_variants(entry.get("DOI")):
        queries.append(doi_query(doi_values))
    if isbn_values := identifier_variants(entry.get("ISBN")):
        queries.append(identifier_query("ISBN", isbn_values))
    return queries


def duplicate_supporting_identifier_queries(entry: dict) -> Sequence[dict]:
    if issn_values := identifier_variants(entry.get("ISSN")):
        return [identifier_query("ISSN", issn_values)]
    return []


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


def doi_query(values: Sequence[str]) -> dict:
    clauses: list[dict[str, Any]] = [{"DOI": {"$in": list(values)}}]
    clauses.extend(
        {"DOI": {"$regex": f"^{re.escape(value)}$", "$options": "i"}}
        for value in values
    )
    return {"$or": clauses}


def identifier_query(field_name: str, values: Sequence[str]) -> dict:
    normalized_values = {
        normalized for value in values if (normalized := normalize_identifier(value))
    }
    patterns = [identifier_pattern(value) for value in sorted(normalized_values)]
    clauses: list[dict[str, Any]] = [{field_name: {"$in": list(values)}}]
    clauses.extend({field_name: {"$regex": pattern}} for pattern in patterns)
    return {"$or": clauses}


def identifier_pattern(value: str) -> str:
    separator = r"[^0-9A-Za-z]*"
    characters = [
        "[Xx]" if character == "X" else re.escape(character) for character in value
    ]
    return f"^{separator}{separator.join(characters)}{separator}$"


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
