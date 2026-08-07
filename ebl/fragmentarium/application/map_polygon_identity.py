from __future__ import annotations

import re
import unicodedata

from ebl.fragmentarium.application.map_geometry import (
    Rings,
    canonical_geometry_checksum,
)


def contains_control_character(value: str) -> bool:
    return any(unicodedata.category(character) == "Cc" for character in value)


def slugify(name: str) -> str:
    slug = re.sub(
        r"[^a-z0-9]+",
        "-",
        unicodedata.normalize("NFKC", name).casefold(),
    ).strip("-")
    if slug:
        return slug
    return "u" + "-".join(f"{ord(character):04x}" for character in name)


def build_polygon_id(prefix: str, name: str, canonical_rings: Rings) -> tuple[str, str]:
    if contains_control_character(name):
        raise ValueError(f"Polygon name contains a control character: {name!r}")
    checksum = canonical_geometry_checksum(canonical_rings)
    return f"{prefix}-{slugify(name)}-{checksum}", checksum


def polygon_match_key(name: str) -> str:
    return re.sub(r"^\d+", "", unicodedata.normalize("NFKC", name).strip())


def normalize_label(value: str) -> str:
    normalized = unicodedata.normalize("NFKC", value).strip().replace("?", "")
    return re.sub(r"\s+", " ", normalized).casefold()
