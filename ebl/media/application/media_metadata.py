"""Bounded contribution metadata validation at the application boundary."""

from typing import Any

from ebl.common.domain.project import ResearchProject
from ebl.errors import DataError
from ebl.media.application.media_metadata_text import (
    valid_text,
    validate_upload_metadata,
)

TEXT_FIELDS = {
    "caption",
    "attribution",
    "creator",
    "sourceInstitution",
    "copyrightHolder",
    "rightsStatement",
    "description",
}
UPLOAD_FIELDS = TEXT_FIELDS | {
    "originalFilename",
    "type",
    "permissionAttested",
    "references",
    "projects",
}
RIGHTS_FIELDS = {"rightsStatement", "permissionAttested", "copyrightHolder"}


def _validate_text(data: dict, *, upload: bool) -> None:
    for field in TEXT_FIELDS | {"originalFilename"}:
        if field in data and not valid_text(data[field], 4000):
            raise DataError(f"{field} must be text of at most 4000 characters.")
    if "rightsStatement" in data and not data["rightsStatement"].strip():
        raise DataError("Rights statement must not be blank.")
    if not upload and "caption" in data and not data["caption"].strip():
        raise DataError("Caption must not be blank.")


def _valid_reference(reference: Any) -> bool:
    if not isinstance(reference, dict) or set(reference) != {"id"}:
        return False
    identifier = reference["id"]
    if not valid_text(identifier, 200):
        return False
    return bool(identifier.strip())


def _validate_references(references: Any) -> None:
    if not isinstance(references, list) or len(references) > 100:
        raise DataError("References must be a list of bibliography identifiers.")
    if not all(_valid_reference(reference) for reference in references):
        raise DataError("References must be a list of bibliography identifiers.")


def _validate_projects(projects: Any) -> None:
    if not isinstance(projects, list) or len(projects) > len(ResearchProject):
        raise DataError("Unknown research project.")
    if not all(
        isinstance(project, str) and project in ResearchProject.__members__
        for project in projects
    ):
        raise DataError("Unknown research project.")


def validate_metadata(data: Any, *, upload: bool = False) -> dict:
    if not isinstance(data, dict) or set(data) - UPLOAD_FIELDS:
        raise DataError("Unknown or invalid media metadata fields.")
    if not upload and "originalFilename" in data:
        raise DataError("Original files cannot be replaced through metadata editing.")
    _validate_text(data, upload=upload)
    if "type" in data and (
        not isinstance(data["type"], str) or data["type"] not in {"PHOTO", "COPY"}
    ):
        raise DataError("Image type must be PHOTO or COPY.")
    if "permissionAttested" in data and data["permissionAttested"] is not True:
        raise DataError("Permission attestation must be explicitly confirmed.")
    if "references" in data:
        _validate_references(data["references"])
    if "projects" in data:
        _validate_projects(data["projects"])
    if upload:
        validate_upload_metadata(data)
    return dict(data)
