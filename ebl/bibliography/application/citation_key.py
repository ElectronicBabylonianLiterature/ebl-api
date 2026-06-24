from __future__ import annotations

import re
import unicodedata
from itertools import count
from typing import Any, Iterable, Mapping, Optional

TITLE_STOPWORDS = {
    "a",
    "an",
    "and",
    "der",
    "die",
    "das",
    "de",
    "des",
    "du",
    "in",
    "l",
    "of",
    "the",
    "und",
    "von",
    "zu",
}


def generate_citation_key(entry: Mapping[str, Any]) -> str:
    creator = creator_token(entry) or "anon"
    year = year_token(entry) or "nd"
    title = title_token(entry) or "untitled"
    return f"{creator}{year}{title}"


def unique_citation_key(entry: Mapping[str, Any], existing_keys: Iterable[str]) -> str:
    base_key = generate_citation_key(entry)
    existing = set(existing_keys)
    if base_key not in existing:
        return base_key
    for suffix in count(2):
        candidate = f"{base_key}-{suffix}"
        if candidate not in existing:
            return candidate
    raise RuntimeError("Unable to generate citation key.")


def creator_token(entry: Mapping[str, Any]) -> str:
    people = entry.get("author") or entry.get("editor") or []
    if people and isinstance(people[0], Mapping):
        creator = people[0].get("family") or people[0].get("literal")
        if isinstance(creator, str):
            return normalize_token(creator)
    return ""


def year_token(entry: Mapping[str, Any]) -> str:
    try:
        year = entry.get("issued", {}).get("date-parts", [[]])[0][0]
    except (IndexError, TypeError, AttributeError):
        return ""
    return str(year) if year is not None else ""


def title_token(entry: Mapping[str, Any]) -> str:
    title = entry.get("title")
    if not isinstance(title, str):
        return ""
    tokens = normalize_words(title)
    content_tokens = [token for token in tokens if token not in TITLE_STOPWORDS]
    return (content_tokens or tokens)[0].title() if tokens else ""


def normalize_words(value: str) -> list[str]:
    normalized = strip_diacritics(value).casefold()
    return re.findall(r"[a-z0-9]+", normalized)


def normalize_token(value: Optional[str]) -> str:
    if not value:
        return ""
    return "".join(
        word.title() if index else word
        for index, word in enumerate(normalize_words(value))
    )


def strip_diacritics(value: str) -> str:
    return (
        unicodedata.normalize("NFKD", value).encode("ascii", "ignore").decode("ascii")
    )
