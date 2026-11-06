from typing import Callable

import pytest
from falcon import testing

from ebl.tests.media.web.helpers import get

from ebl.common.domain.scopes import Scope
from ebl.context import Context
from ebl.media.application.media_stored import StoredMedia
from ebl.tests.factories.fragment import FragmentFactory
from ebl.tests.media.in_memory_media import InMemoryMediaRepository
from ebl.transliteration.domain.museum_number import MuseumNumber


@pytest.fixture
def restricted_media(
    media_context: Context,
    create_media: Callable[..., StoredMedia],
) -> StoredMedia:
    stored = create_media()
    fragment = media_context.fragment_repository.query_by_museum_number(
        MuseumNumber.of("K.1")
    )
    media_context.fragment_repository.update_field(
        "authorized_scopes", fragment.set_scopes([Scope.READ_CAIC_FRAGMENTS])
    )
    return stored


@pytest.fixture
def deny_media_reads(
    media_repository: InMemoryMediaRepository, monkeypatch: pytest.MonkeyPatch
) -> Callable[[], None]:
    def forbidden_lookup(*_args: object) -> None:
        raise AssertionError("Unauthorized request reached media lookup.")

    def deny() -> None:
        monkeypatch.setattr(media_repository, "find_by_fragment", forbidden_lookup)
        monkeypatch.setattr(
            media_repository, "find_stored_in_fragment", forbidden_lookup
        )

    return deny


@pytest.mark.parametrize("suffix", ["", "/file", "/display", "/thumbnail/small"])
def test_guest_cannot_read_restricted_media(
    guest_media_client: testing.TestClient,
    media_client: testing.TestClient,
    restricted_media: StoredMedia,
    deny_media_reads: Callable[[], None],
    suffix: str,
) -> None:
    stored = restricted_media
    path = f"/media/{stored.media.id}{suffix}" if suffix else "/media"
    path += "?fragment=K.1"
    assert get(media_client, path).status_code == 200

    deny_media_reads()
    assert get(guest_media_client, path).status_code == 403


def test_binary_cannot_be_read_through_another_fragment(
    media_client: testing.TestClient,
    media_context: Context,
    create_media: Callable[..., StoredMedia],
) -> None:
    stored = create_media()
    media_context.fragment_repository.create(
        FragmentFactory.build(number=MuseumNumber.of("K.2"), references=())
    )
    response = get(media_client, f"/media/{stored.media.id}/file?fragment=K.2")
    assert response.status_code == 404


def test_unknown_fragment_cannot_expose_orphaned_media(
    media_client: testing.TestClient, create_media: Callable[..., StoredMedia]
) -> None:
    stored = create_media()
    assert get(media_client, "/media?fragment=K.999").status_code == 404
    assert (
        get(media_client, f"/media/{stored.media.id}/file?fragment=K.999").status_code
        == 404
    )


@pytest.mark.parametrize("path", ["/media", "/media/invalid/file"])
def test_fragment_parameter_is_required(
    media_client: testing.TestClient, path: str
) -> None:
    assert get(media_client, path).status_code == 400


@pytest.mark.parametrize("fragment", ["invalid", ""])
def test_invalid_fragment_is_client_error(
    media_client: testing.TestClient, fragment: str
) -> None:
    assert get(media_client, f"/media?fragment={fragment}").status_code in {
        400,
        422,
    }


def test_invalid_media_identifier_is_client_error(
    media_client: testing.TestClient, create_media: Callable[..., StoredMedia]
) -> None:
    create_media()
    assert get(media_client, "/media/invalid/file?fragment=K.1").status_code == 422


def test_duplicate_fragment_parameter_is_rejected(
    media_client: testing.TestClient,
) -> None:
    assert get(media_client, "/media?fragment=K.1&fragment=K.2").status_code == 422
