from __future__ import annotations

import re
import unicodedata
from itertools import count
from typing import Any, Callable, Iterable, Mapping, Optional, Sequence

from ebl.bibliography.application.citation_key import (
    creator_token,
    generate_citation_key,
    title_token,
    year_token,
)
from ebl.errors import DataError

DEFAULT_BIBLIOGRAPHY_ID_START = 30000000
BIBLIOGRAPHY_ID_PREFIX = "Q"
PARTNER_ALIAS_TYPE = "partner_id"
PARTNER_ALIAS_SOURCE = "partner_request"
PARTNER_ALIAS_STATUS = "redirect"
_ASCII_APOSTROPHES = str.maketrans(
    {
        "\u2018": "'",
        "\u2019": "'",
        "\u02bb": "'",
        "\u02bc": "'",
        "\uff07": "'",
    }
)
_ASCII_DASHES = str.maketrans(
    {
        "\u2010": "-",
        "\u2011": "-",
        "\u2012": "-",
        "\u2013": "-",
        "\u2014": "-",
        "\u2015": "-",
        "\u2212": "-",
    }
)
_BIBLIOGRAPHY_ID_PATTERN = re.compile(rf"^{BIBLIOGRAPHY_ID_PREFIX}(\d+)$")


def create_partner_alias(value: str) -> dict[str, str]:
    validate_partner_id(value)
    normalized_value = normalize_partner_id(value)
    if not normalized_value:
        raise DataError(
            "Partner bibliography id must contain at least one letter or digit."
        )
    return {
        "value": value,
        "normalizedValue": normalized_value,
        "type": PARTNER_ALIAS_TYPE,
        "source": PARTNER_ALIAS_SOURCE,
        "status": PARTNER_ALIAS_STATUS,
    }


def validate_partner_id(value: Any) -> None:
    if not isinstance(value, str) or not value.strip():
        raise DataError("Partner bibliography id must be a non-empty string.")
    if any(unicodedata.category(character).startswith("C") for character in value):
        raise DataError(
            "Partner bibliography id must not contain null bytes or control characters."
        )


def normalize_partner_id(value: str) -> str:
    normalized = unicodedata.normalize("NFKC", value)
    normalized = normalized.translate(_ASCII_APOSTROPHES).translate(_ASCII_DASHES)
    normalized = (
        unicodedata.normalize("NFKD", normalized)
        .encode("ascii", "ignore")
        .decode("ascii")
    )
    return re.sub(r"[^a-z0-9]+", "-", normalized.casefold()).strip("-")


def canonical_bibliography_id_candidates(existing_ids: Sequence[str]) -> Iterable[str]:
    width = len(str(DEFAULT_BIBLIOGRAPHY_ID_START))
    max_numeric_id = DEFAULT_BIBLIOGRAPHY_ID_START - 1

    for id_ in existing_ids:
        if match := _BIBLIOGRAPHY_ID_PATTERN.fullmatch(id_):
            width = max(width, len(match.group(1)))
            max_numeric_id = max(max_numeric_id, int(match.group(1)))

    for numeric_id in count(max_numeric_id + 1):
        yield f"{BIBLIOGRAPHY_ID_PREFIX}{numeric_id:0{width}d}"


def select_canonical_bibliography_id(
    existing_ids: Sequence[str],
    lookup_value_exists: Callable[[str], bool],
    reserved_values: Sequence[str] = (),
) -> str:
    reserved = set(reserved_values)
    for candidate in canonical_bibliography_id_candidates(existing_ids):
        if candidate in reserved or lookup_value_exists(candidate):
            continue
        return candidate
    raise RuntimeError("Unable to generate bibliography id.")


def generate_partner_citation_key(
    entry: Mapping[str, Any],
    lookup_value_exists: Callable[[str], bool],
) -> Optional[str]:
    if not has_meaningful_citation_key_data(entry):
        return None

    base_key = generate_citation_key(entry)
    for suffix in count(1):
        candidate = base_key if suffix == 1 else f"{base_key}-{suffix}"
        if not lookup_value_exists(candidate):
            return candidate
    raise RuntimeError("Unable to generate citation key.")


def has_meaningful_citation_key_data(entry: Mapping[str, Any]) -> bool:
    return bool(creator_token(entry) and year_token(entry) and title_token(entry))
