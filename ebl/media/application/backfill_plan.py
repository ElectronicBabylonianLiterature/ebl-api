from typing import Mapping

import attr

from ebl.media.domain import MediaChecksum, MediaRepresentation


@attr.s(auto_attribs=True, frozen=True)
class BackfillPolicy:
    generate_previews: bool = False
    map_attribution: bool = True
    max_file_size: int = 536_870_912
    max_pixels: int = 40_000_000

    def __attrs_post_init__(self) -> None:
        if (
            type(self.generate_previews) is not bool
            or type(self.map_attribution) is not bool
        ):
            raise ValueError("Migration switches must be boolean.")
        if (
            type(self.max_file_size) is not int
            or not 1 <= self.max_file_size <= 536_870_912
        ):
            raise ValueError("Migration byte limit must be between 1 and 536870912.")
        if type(self.max_pixels) is not int or not 1 <= self.max_pixels <= 40_000_000:
            raise ValueError("Migration pixel limit must be between 1 and 40000000.")

    def document(self) -> dict:
        return {
            "generatePreviews": self.generate_previews,
            "mapAttribution": self.map_attribution,
            "maxFileSize": self.max_file_size,
            "maxPixels": self.max_pixels,
            "primaryPolicy": "preserve",
        }

    @classmethod
    def of(cls, document: Mapping) -> "BackfillPolicy":
        if document.get("primaryPolicy") != "preserve":
            raise ValueError("Only the preserve primary policy is supported.")
        try:
            return cls(
                document["generatePreviews"],
                document["mapAttribution"],
                document["maxFileSize"],
                document["maxPixels"],
            )
        except KeyError as error:
            raise ValueError("Migration policy is incomplete.") from error


@attr.s(auto_attribs=True, frozen=True)
class InspectedPhoto:
    fragment_id: str
    representation: MediaRepresentation
    attribution: str | None
    attribution_evidence: Mapping[str, str]
    binary_validation: str

    def document(self) -> dict:
        representation = self.representation
        return {
            "fragmentId": self.fragment_id,
            "representation": {
                "mimeType": representation.mime_type,
                "width": representation.width,
                "height": representation.height,
                "fileSize": representation.file_size,
                "sha256": representation.checksum.value
                if representation.checksum
                else None,
            },
            "attribution": self.attribution,
            "attributionEvidence": dict(self.attribution_evidence),
            "binaryValidation": self.binary_validation,
        }

    @classmethod
    def of(cls, document: Mapping) -> "InspectedPhoto":
        representation = document["representation"]
        return cls(
            document["fragmentId"],
            MediaRepresentation(
                representation["mimeType"],
                representation["width"],
                representation["height"],
                representation["fileSize"],
                MediaChecksum(value=representation["sha256"]),
            ),
            document["attribution"],
            document["attributionEvidence"],
            document["binaryValidation"],
        )


@attr.s(auto_attribs=True, frozen=True)
class RejectedSource:
    source_id: str
    snapshot: str
    filename: str
    outcome: str
    reason: str | None

    def document(self) -> dict:
        return {
            "sourceId": self.source_id,
            "snapshot": self.snapshot,
            "filename": self.filename,
            "outcome": self.outcome,
            "reason": self.reason,
        }

    @classmethod
    def of(cls, document: Mapping) -> "RejectedSource":
        if set(document) != {"sourceId", "snapshot", "filename", "outcome", "reason"}:
            raise ValueError("Rejected source fields are incomplete or malformed.")
        return cls(
            document["sourceId"],
            document["snapshot"],
            document["filename"],
            document["outcome"],
            document["reason"],
        )


@attr.s(auto_attribs=True, frozen=True)
class PlannedPhoto:
    source_id: str
    snapshot: str
    filename: str
    outcome: str
    reason: str | None = None
    inspected_photos: tuple[InspectedPhoto, ...] = ()

    @property
    def rejected_sources(self) -> tuple[RejectedSource, ...]:
        return (
            ()
            if self.inspected_photos
            else (
                RejectedSource(
                    self.source_id,
                    self.snapshot,
                    self.filename,
                    self.outcome,
                    self.reason,
                ),
            )
        )

    @property
    def fragment_id(self) -> str | None:
        return self.inspected_photos[0].fragment_id if self.inspected_photos else None

    @property
    def representation(self) -> MediaRepresentation | None:
        return (
            self.inspected_photos[0].representation if self.inspected_photos else None
        )

    @property
    def attribution(self) -> str | None:
        return self.inspected_photos[0].attribution if self.inspected_photos else None

    @property
    def attribution_evidence(self) -> Mapping[str, str]:
        return (
            self.inspected_photos[0].attribution_evidence
            if self.inspected_photos
            else {}
        )

    @property
    def binary_validation(self) -> str | None:
        return (
            self.inspected_photos[0].binary_validation
            if self.inspected_photos
            else None
        )

    def document(self) -> dict:
        return {
            "kind": "photo",
            "sourceId": self.source_id,
            "snapshot": self.snapshot,
            "filename": self.filename,
            "outcome": self.outcome,
            "reason": self.reason,
            "inspectedPhotos": [photo.document() for photo in self.inspected_photos],
            "rejectedSources": [source.document() for source in self.rejected_sources],
        }

    @classmethod
    def of(cls, document: Mapping) -> "PlannedPhoto":
        return cls(
            document["sourceId"],
            document["snapshot"],
            document["filename"],
            document["outcome"],
            document["reason"],
            tuple(InspectedPhoto.of(photo) for photo in document["inspectedPhotos"]),
        )


class SourceRejected(ValueError):
    def __init__(self, outcome: str, reason: str) -> None:
        super().__init__(outcome, reason)
        self.outcome = outcome
        self.reason = reason

    def __str__(self) -> str:
        return self.reason
