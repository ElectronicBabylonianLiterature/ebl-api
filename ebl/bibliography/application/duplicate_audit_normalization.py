from __future__ import annotations

import re
import unicodedata
from dataclasses import dataclass
from typing import Any, Mapping, Optional

PROJECTION = {
    "_id": 1,
    "type": 1,
    "title": 1,
    "title-short": 1,
    "author": 1,
    "editor": 1,
    "issued": 1,
    "DOI": 1,
    "ISBN": 1,
    "ISSN": 1,
    "language": 1,
    "container-title": 1,
    "container-title-short": 1,
    "collection-title": 1,
    "collection-number": 1,
    "publisher": 1,
    "volume": 1,
    "issue": 1,
    "page": 1,
    "page-first": 1,
    "edition": 1,
}


def normalize_doi(value: Any) -> str:
    if not isinstance(value, str):
        return ""
    value = value.strip().casefold()
    value = re.sub(r"^doi:\s*", "", value)
    value = re.sub(r"^https?://(dx\.)?doi\.org/", "", value)
    value = value.strip()
    if value in {"", "-", "--", "n/a", "na", "none", "null", "pending", "<>"}:
        return ""
    if re.search(r"[<>\s]", value) or not re.match(r"^10\.\d+/\S+$", value):
        return ""
    return value


def normalize_identifier(value: Any) -> str:
    if not isinstance(value, str):
        return ""
    return re.sub(r"[^0-9xX]", "", value).upper()


def normalize_isbn(value: Any) -> str:
    normalized = normalize_identifier(value)
    if len(normalized) == 10 and re.match(r"^\d{9}[\dX]$", normalized):
        return normalized
    if len(normalized) == 13 and normalized.isdigit():
        return normalized
    return ""


def normalize_issn(value: Any) -> str:
    normalized = normalize_identifier(value)
    if len(normalized) == 8 and re.match(r"^\d{7}[\dX]$", normalized):
        return normalized
    return ""


def normalize_text(value: Any, *, fold_diacritics: bool = True) -> str:
    if not isinstance(value, str):
        return ""
    if fold_diacritics:
        value = (
            unicodedata.normalize("NFKD", value)
            .encode("ascii", "ignore")
            .decode("ascii")
        )
    else:
        value = unicodedata.normalize("NFKC", value)
    value = value.casefold()
    value = re.sub(r"[^\w]+", " ", value, flags=re.UNICODE)
    return re.sub(r"\s+", " ", value).strip()


def normalize_short_field(value: Any) -> str:
    if value is None:
        return ""
    text = re.sub(r"[\u2010-\u2015]", "-", str(value))
    return normalize_text(text, fold_diacritics=True)


def title_tokens(title: str) -> set[str]:
    stopwords = {
        "a",
        "an",
        "and",
        "der",
        "die",
        "das",
        "de",
        "des",
        "du",
        "for",
        "in",
        "of",
        "on",
        "the",
        "und",
        "von",
        "zu",
    }
    return {
        token for token in title.split() if len(token) > 1 and token not in stopwords
    }


def extract_year(entry: Mapping[str, Any]) -> Optional[int]:
    try:
        year = entry.get("issued", {}).get("date-parts", [[]])[0][0]
    except (IndexError, KeyError, TypeError):
        return None
    try:
        return int(year)
    except (TypeError, ValueError):
        return None


def normalize_name(name: Mapping[str, Any]) -> str:
    family = normalize_text(name.get("family"))
    literal = normalize_text(name.get("literal"))
    given = normalize_text(name.get("given"))
    initials = "".join(part[0] for part in given.split() if part)
    return "|".join(part for part in (family or literal, initials) if part)


def contributor_names(entry: Mapping[str, Any]) -> tuple[str, ...]:
    people = entry.get("author") or entry.get("editor") or ()
    return tuple(
        normalized for person in people if (normalized := normalize_name(person))
    )


def primary_family(entry: Mapping[str, Any]) -> str:
    names = contributor_names(entry)
    return names[0].split("|", 1)[0] if names else ""


@dataclass(frozen=True)
class NormalizedBibliographyEntry:
    id: str
    raw: Mapping[str, Any]
    type: str
    title: str
    title_tokens: set[str]
    contributors: tuple[str, ...]
    primary_family: str
    year: Optional[int]
    doi: str
    isbn: str
    issn: str
    container_title: str
    container_title_short: str
    collection_title: str
    publisher: str
    volume: str
    issue: str
    page: str
    page_first: str
    edition: str
    language: str


def normalize_entry(entry: Mapping[str, Any]) -> NormalizedBibliographyEntry:
    id_ = str(entry.get("_id") or entry.get("id") or "")
    normalized_title = normalize_text(entry.get("title"))
    return NormalizedBibliographyEntry(
        id=id_,
        raw=entry,
        type=str(entry.get("type") or ""),
        title=normalized_title,
        title_tokens=title_tokens(normalized_title),
        contributors=contributor_names(entry),
        primary_family=primary_family(entry),
        year=extract_year(entry),
        doi=normalize_doi(entry.get("DOI")),
        isbn=normalize_isbn(entry.get("ISBN")),
        issn=normalize_issn(entry.get("ISSN")),
        container_title=normalize_text(entry.get("container-title")),
        container_title_short=normalize_text(entry.get("container-title-short")),
        collection_title=normalize_text(entry.get("collection-title")),
        publisher=normalize_text(entry.get("publisher")),
        volume=normalize_short_field(entry.get("volume")),
        issue=normalize_short_field(entry.get("issue")),
        page=normalize_short_field(entry.get("page")),
        page_first=normalize_short_field(entry.get("page-first")),
        edition=normalize_short_field(entry.get("edition")),
        language=normalize_text(entry.get("language")),
    )
