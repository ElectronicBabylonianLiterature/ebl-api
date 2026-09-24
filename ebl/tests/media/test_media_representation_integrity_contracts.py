from io import BytesIO

import attr
import pytest

from ebl.media.application import (
    DisplayRepresentationWriteRequest,
    OpenRepresentation,
    OriginalRepresentationWriteRequest,
)
from ebl.media.domain import MediaId
from ebl.tests.media.factories import (
    display_representation,
    original_representation,
)
from ebl.tests.media.in_memory_media import InMemoryRepresentationStore
from ebl.tests.media.representation_helpers import representation_for_content

PHOTO_ID = MediaId("550e8400-e29b-41d4-a716-446655440000")
CONTENT = b"media-bytes"


def test_open_representation_carries_verified_metadata() -> None:
    representation = representation_for_content(CONTENT, original_representation())
    opened = OpenRepresentation(
        media_id=PHOTO_ID,
        representation=representation,
        content=BytesIO(CONTENT),
        length=len(CONTENT),
    )

    assert opened.content.read() == CONTENT
    assert opened.representation.mime_type == representation.mime_type
    assert not hasattr(opened, "content_type")


def test_open_representation_rejects_a_metadata_length_mismatch() -> None:
    representation = representation_for_content(CONTENT, original_representation())

    with pytest.raises(ValueError, match="length must match"):
        OpenRepresentation(PHOTO_ID, representation, BytesIO(CONTENT), length=1)


def test_store_rejects_a_byte_count_mismatch() -> None:
    representation = representation_for_content(CONTENT, original_representation())
    mismatched = attr.evolve(representation, file_size=len(CONTENT) + 1)

    with pytest.raises(ValueError, match="byte count must match"):
        InMemoryRepresentationStore().write_original(
            OriginalRepresentationWriteRequest(PHOTO_ID, BytesIO(CONTENT), mismatched)
        )


def test_store_rejects_an_original_checksum_mismatch() -> None:
    representation = original_representation()
    mismatched = attr.evolve(representation, file_size=len(CONTENT))

    with pytest.raises(ValueError, match="checksum must match"):
        InMemoryRepresentationStore().write_original(
            OriginalRepresentationWriteRequest(PHOTO_ID, BytesIO(CONTENT), mismatched)
        )


def test_store_rejects_a_preview_byte_count_mismatch() -> None:
    mismatched = attr.evolve(display_representation(), file_size=len(CONTENT) + 1)

    with pytest.raises(ValueError, match="byte count must match"):
        InMemoryRepresentationStore().write_display(
            DisplayRepresentationWriteRequest(PHOTO_ID, BytesIO(CONTENT), mismatched)
        )
