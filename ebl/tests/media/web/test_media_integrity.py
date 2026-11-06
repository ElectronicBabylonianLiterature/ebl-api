from io import BytesIO
from typing import Callable

import attr
import pytest
from falcon import testing

from ebl.media.application.media_stored import OpenRepresentation, StoredMedia
from ebl.media.application.media_storage_identity import StoredRepresentationHandle
from ebl.media.domain import MediaId
from ebl.tests.media.in_memory_media import InMemoryRepresentationStore
from ebl.tests.media.web.helpers import get


def test_missing_bytes_are_an_integrity_error(
    media_client: testing.TestClient,
    create_media: Callable[..., StoredMedia],
    media_store: InMemoryRepresentationStore,
) -> None:
    stored = create_media()
    media_store.delete_representation(stored.representations.original)
    result = get(media_client, f"/media/{stored.media.id}/file?fragment=K.1")
    assert result.status_code == 500
    assert stored.representations.original.value not in result.text


@pytest.mark.parametrize("mismatch", ["owner", "representation"])
def test_mismatched_opened_metadata_closes_stream(
    media_client: testing.TestClient,
    create_media: Callable[..., StoredMedia],
    media_store: InMemoryRepresentationStore,
    monkeypatch: pytest.MonkeyPatch,
    mismatch: str,
) -> None:
    stored = create_media()
    content = BytesIO(b"original")

    def open_invalid(handle: StoredRepresentationHandle) -> OpenRepresentation:
        representation = handle.representation
        if mismatch == "representation":
            representation = attr.evolve(representation, width=representation.width + 1)
        return OpenRepresentation(
            MediaId("550e8400-e29b-41d4-a716-446655440005")
            if mismatch == "owner"
            else stored.media.id,
            representation,
            content,
            len(b"original"),
        )

    monkeypatch.setattr(media_store, "open_representation", open_invalid)
    assert (
        get(media_client, f"/media/{stored.media.id}/file?fragment=K.1").status_code
        == 500
    )
    assert content.closed


def test_successful_binary_response_closes_stream(
    media_client: testing.TestClient,
    create_media: Callable[..., StoredMedia],
    media_store: InMemoryRepresentationStore,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    stored = create_media()
    content = BytesIO(b"original")

    def open_tracked(handle: StoredRepresentationHandle) -> OpenRepresentation:
        return OpenRepresentation(stored.media.id, handle.representation, content, 8)

    monkeypatch.setattr(media_store, "open_representation", open_tracked)
    result = get(media_client, f"/media/{stored.media.id}/file?fragment=K.1")
    assert result.status_code == 200
    assert result.content == b"original"
    assert content.closed
