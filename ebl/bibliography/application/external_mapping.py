from __future__ import annotations

from typing import Any, Mapping, Optional, TypedDict
from urllib.parse import urlparse


class NormalizedExternalMapping(TypedDict):
    partner: str
    externalId: str
    externalUrl: Optional[str]
    bibliographyId: Optional[str]


def normalize_external_mapping(mapping: Mapping[str, Any]) -> NormalizedExternalMapping:
    partner = normalized_required_string(mapping, "partner")
    external_id = normalized_required_string(mapping, "externalId")
    bibliography_id = normalized_optional_string(mapping.get("bibliographyId"))
    external_url = normalized_optional_url(mapping.get("externalUrl"))
    return {
        "partner": partner,
        "externalId": external_id,
        "externalUrl": external_url,
        "bibliographyId": bibliography_id,
    }


def external_mapping_key(mapping: Mapping[str, Any]) -> tuple[str, str]:
    normalized = normalize_external_mapping(mapping)
    return normalized["partner"], normalized["externalId"]


def normalized_required_string(mapping: Mapping[str, Any], field_name: str) -> str:
    value = normalized_optional_string(mapping.get(field_name))
    if not value:
        raise ValueError(f"{field_name} is required.")
    return value


def normalized_optional_string(value: Any) -> Optional[str]:
    if value is None:
        return None
    if not isinstance(value, str):
        raise ValueError("Expected string value.")
    normalized = value.strip()
    return normalized or None


def normalized_optional_url(value: Any) -> Optional[str]:
    normalized = normalized_optional_string(value)
    if normalized is None:
        return None
    parsed = urlparse(normalized)
    if parsed.scheme not in {"http", "https"} or not parsed.netloc:
        raise ValueError("externalUrl must be an HTTP or HTTPS URL.")
    return normalized
