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
class PlannedPhoto:
    source_id: str
    snapshot: str
    filename: str
    fragment_id: str | None
    outcome: str
    reason: str | None = None
    representation: MediaRepresentation | None = None
    attribution: str | None = None
    attribution_evidence: Mapping[str, str] = attr.ib(factory=dict)
    binary_validation: str | None = None

    def document(self) -> dict:
        representation = self.representation
        return {
            "kind": "photo",
            "sourceId": self.source_id,
            "snapshot": self.snapshot,
            "filename": self.filename,
            "fragmentId": self.fragment_id,
            "outcome": self.outcome,
            "reason": self.reason,
            "representation": (
                {
                    "mimeType": representation.mime_type,
                    "width": representation.width,
                    "height": representation.height,
                    "fileSize": representation.file_size,
                    "sha256": (
                        representation.checksum.value
                        if representation.checksum is not None
                        else None
                    ),
                }
                if representation is not None
                else None
            ),
            "attribution": self.attribution,
            "attributionEvidence": dict(self.attribution_evidence),
            "binaryValidation": self.binary_validation,
        }

    @classmethod
    def of(cls, document: Mapping) -> "PlannedPhoto":
        representation = document.get("representation")
        return cls(
            source_id=document["sourceId"],
            snapshot=document["snapshot"],
            filename=document["filename"],
            fragment_id=document["fragmentId"],
            outcome=document["outcome"],
            reason=document["reason"],
            representation=(
                MediaRepresentation(
                    representation["mimeType"],
                    representation["width"],
                    representation["height"],
                    representation["fileSize"],
                    MediaChecksum(value=representation["sha256"]),
                )
                if representation is not None
                else None
            ),
            attribution=document["attribution"],
            attribution_evidence=document["attributionEvidence"],
            binary_validation=document["binaryValidation"],
        )


class SourceRejected(ValueError):
    def __init__(self, outcome: str, reason: str) -> None:
        super().__init__(outcome, reason)
        self.outcome = outcome
        self.reason = reason

    def __str__(self) -> str:
        return self.reason
