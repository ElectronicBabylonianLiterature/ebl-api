from typing import Mapping

from ebl.media.application.backfill_plan import BackfillPolicy, PlannedPhoto
from ebl.media.infrastructure.backfill_candidates import candidate_media


def validate_plan_header(header: Mapping) -> None:
    if not all(
        isinstance(header.get(key), str) and header[key]
        for key in ("database", "endpointSha256")
    ) or not isinstance(header.get("policy"), dict):
        raise ValueError("Plan must bind an explicit target and policy.")
    BackfillPolicy.of(header["policy"])


def validate_plan_photo(document: Mapping) -> None:
    required_strings = ("sourceId", "snapshot", "filename", "outcome")
    optional_strings = ("fragmentId", "reason", "attribution", "binaryValidation")
    if not all(isinstance(document.get(key), str) for key in required_strings):
        raise ValueError("Plan photo fields must have their declared types.")
    if not all(
        document.get(key) is None or isinstance(document[key], str)
        for key in optional_strings
    ):
        raise ValueError("Optional plan photo fields must be text or null.")
    if document["outcome"] not in {
        "candidate",
        "already-present",
        "blocked",
        "review",
        "conflicting",
    }:
        raise ValueError("Plan photo outcome is unsupported.")
    evidence = document.get("attributionEvidence")
    if not isinstance(evidence, dict) or not all(
        isinstance(key, str) and isinstance(value, str)
        for key, value in evidence.items()
    ):
        raise ValueError("Attribution evidence must preserve text values.")
    try:
        photo = PlannedPhoto.of(document)
        if photo.outcome in {"candidate", "already-present"}:
            candidate_media(photo)
    except (KeyError, TypeError) as error:
        raise ValueError("Plan photo is incomplete or malformed.") from error
