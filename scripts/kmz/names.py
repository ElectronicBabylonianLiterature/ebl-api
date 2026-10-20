from __future__ import annotations

import re
import unicodedata

from ebl.provenance.domain.provenance_model import ProvenanceRecord

_IGNORABLE_APOSTROPHES = str.maketrans(
    "",
    "",
    "'`\u00b4\u02bb\u02bc\u02be\u02bf\u2018\u2019\u201b",
)


_SPACE_RE = re.compile(r"\s+")


_PARENTHETICAL_RE = re.compile(r"\(([^()]*)\)")


_BROAD_REGION_NAMES = {
    "akkad",
    "anatolia",
    "arabia",
    "assyria",
    "babylonia",
    "egypt",
    "elam",
    "hatti",
    "iran",
    "levant",
    "mesopotamia",
    "northern babylonia",
    "palestine",
    "periphery",
    "southern babylonia",
    "subartu",
    "sumer",
    "syria",
    "urartu",
}


_BROAD_REGION_IDS = {
    name.upper()
    for name in _BROAD_REGION_NAMES
    if name not in {"northern babylonia", "palestine", "southern babylonia"}
}


def normalize_spaces(value: str) -> str:
    return _SPACE_RE.sub(" ", value).strip()


def remove_uncertainty_markers(value: str) -> str:
    return value.replace("?", "")


def basic_name_key(value: str) -> str:
    return normalize_spaces(remove_uncertainty_markers(value)).casefold()


def normalize_name(value: str) -> str:
    cleaned = normalize_spaces(remove_uncertainty_markers(value))
    cleaned = cleaned.translate(_IGNORABLE_APOSTROPHES)
    decomposed = unicodedata.normalize("NFD", cleaned)
    stripped = "".join(
        character for character in decomposed if unicodedata.category(character) != "Mn"
    )
    return normalize_spaces(stripped).casefold()


def extract_name_variants(raw_name: str) -> tuple[str, ...]:
    name = normalize_spaces(raw_name)
    before_parenthesis = name.split("(", 1)[0]
    pieces = [*before_parenthesis.split("/")]
    for parenthetical in _PARENTHETICAL_RE.findall(name):
        pieces.extend(parenthetical.split("/"))

    variants: list[str] = []
    seen: set[str] = set()
    for piece in pieces:
        variant = normalize_spaces(remove_uncertainty_markers(piece))
        if variant and variant not in seen:
            variants.append(variant)
            seen.add(variant)
    return tuple(variants)


def is_broad_region_name(name: str) -> bool:
    return normalize_name(name) in _BROAD_REGION_NAMES


def is_broad_region_record(record: ProvenanceRecord) -> bool:
    return record.id in _BROAD_REGION_IDS or is_broad_region_name(record.long_name)
