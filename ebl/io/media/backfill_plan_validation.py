from typing import Mapping

from ebl.media.application.backfill_plan import (
    BackfillPolicy,
    PlannedPhoto,
    RejectedSource,
)
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
    if not all(isinstance(document.get(key), str) for key in required_strings):
        raise ValueError("Plan photo fields must have their declared types.")
    if document.get("reason") is not None and not isinstance(document["reason"], str):
        raise ValueError("Optional plan photo fields must be text or null.")
    if document["outcome"] not in {
        "candidate",
        "already-present",
        "blocked",
        "review",
        "conflicting",
    }:
        raise ValueError("Plan photo outcome is unsupported.")
    try:
        if set(document) != {
            "kind",
            "sourceId",
            "snapshot",
            "filename",
            "outcome",
            "reason",
            "inspectedPhotos",
            "rejectedSources",
        }:
            raise ValueError("Plan photo is incomplete or malformed.")
        inspected = document["inspectedPhotos"]
        rejected = document["rejectedSources"]
        if not isinstance(inspected, list) or not isinstance(rejected, list):
            raise ValueError(
                "Plan records require separate inspected and rejected arrays."
            )
        if len(inspected) + len(rejected) != 1:
            raise ValueError(
                "Each source must have exactly one inspection or rejection."
            )
        for inspection in inspected:
            _validate_inspection(inspection)
        photo = PlannedPhoto.of(document)
        if photo.outcome in {"candidate", "already-present"}:
            if not photo.inspected_photos:
                raise ValueError("An applicable source must have an inspection.")
            candidate_media(photo)
        for rejection in (RejectedSource.of(value) for value in rejected):
            if (
                rejection.source_id,
                rejection.snapshot,
                rejection.filename,
                rejection.outcome,
                rejection.reason,
            ) != (
                photo.source_id,
                photo.snapshot,
                photo.filename,
                photo.outcome,
                photo.reason,
            ):
                raise ValueError("Rejection differs from its source record.")
    except (KeyError, TypeError) as error:
        raise ValueError("Plan photo is incomplete or malformed.") from error


def _validate_inspection(document: Mapping) -> None:
    if set(document) != {
        "fragmentId",
        "representation",
        "attribution",
        "attributionEvidence",
        "binaryValidation",
    }:
        raise ValueError("Inspection fields are incomplete or malformed.")
    if not all(
        isinstance(document.get(key), str) for key in ("fragmentId", "binaryValidation")
    ):
        raise ValueError("Inspected identity and validation must be text.")
    representation = document["representation"]
    if not isinstance(representation, dict) or set(representation) != {
        "mimeType",
        "width",
        "height",
        "fileSize",
        "sha256",
    }:
        raise ValueError("Inspected representation fields are incomplete or malformed.")
    if document["attribution"] is not None and not isinstance(
        document["attribution"], str
    ):
        raise ValueError("Inspected attribution must be text or null.")
    evidence = document["attributionEvidence"]
    if not isinstance(evidence, dict) or not all(
        isinstance(key, str) and isinstance(value, str)
        for key, value in evidence.items()
    ):
        raise ValueError("Attribution evidence must preserve text values.")
