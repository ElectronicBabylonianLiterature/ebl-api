"""Independent removal tests across canonical media and legacy fallback routes."""

import falcon
from dataclasses import dataclass
import pytest
from typing import cast
from falcon import testing
from gridfs import GridFS

from ebl import error_handler
from ebl.files.infrastructure.grid_fs_file_repository import GridFsFileRepository
from ebl.fragmentarium.web.photo import PhotoResource
from ebl.fragmentarium.application.fragment_finder import FragmentFinder
from ebl.fragmentarium.application.fragment_repository import FragmentRepository
from ebl.media.application.media_stored import StoredMedia, StoredMediaRepresentations
from ebl.media.domain import Media, MediaId, MediaRepresentations, MediaType
from ebl.media.infrastructure.legacy_media_handles import (
    LegacyRepresentationAdoption,
    legacy_import_source,
)
from ebl.media.infrastructure.media_recovery import recover_media
from ebl.media.web.bootstrap import create_media_routes
from ebl.media.web.fragment_media_enricher import FragmentMediaEnricher
from ebl.tests.media.factories import association
from ebl.tests.media.web.helpers import body, get
from ebl.tests.media.infrastructure.persistence_helpers import (
    image_bytes,
    image_representation,
)
from ebl.tests.media.test_media_management_uploads import Fragments, upload
from ebl.transliteration.domain.museum_number import MuseumNumber
from ebl.users.infrastructure.auth0 import Auth0User


def legacy_client(runtime, database, *, manager=False, fragment_access=False):
    permissions = ["manage:fragment_media"] if manager else []
    if fragment_access:
        permissions.append("read:CAIC-fragments")
    user = Auth0User(
        {"sub": "auth0|legacy-reviewer", "scope": " ".join(permissions)},
        lambda: {"name": "Independent local reviewer"},
    )

    class Authentication:
        def process_request(self, req, resp):
            req.context["user"] = user

    class Finder:
        def fetch_scopes(self, number):
            return Fragments().query_read_scopes(number)

        def find_photo(self, number):
            return GridFsFileRepository(database, "photos").query_by_file_name(
                f"{number}.jpg"
            )

        def find_thumbnail(self, number, width):
            return GridFsFileRepository(database, "thumbnails").query_by_file_name(
                f"{number}_{width.value}.jpg"
            )

    app = falcon.App(middleware=[Authentication()])
    error_handler.set_up(app)
    create_media_routes(app, cast(FragmentRepository, Fragments()), runtime)
    resource = PhotoResource(cast(FragmentFinder, Finder()), runtime.service)
    app.add_route("/fragments/{number}/photo", resource)
    app.add_route("/fragments/{number}/thumbnail/{resolution}", resource)
    return testing.TestClient(app)


@dataclass(frozen=True)
class LegacyMediaOptions:
    filename: str = "K.1.jpg"
    original_filename: str | None = None
    associations: tuple | None = None


DEFAULT_LEGACY_MEDIA_OPTIONS = LegacyMediaOptions()


def add_legacy(
    runtime, database, options: LegacyMediaOptions = DEFAULT_LEGACY_MEDIA_OPTIONS
):
    filename, original_filename = options.filename, options.original_filename
    associations = options.associations
    original = image_bytes("JPEG")
    file_id = GridFS(database, "photos").put(
        original, filename=filename, contentType="image/jpeg"
    )
    representation = image_representation(original, "image/jpeg")
    identifier = MediaId.create()
    handle = runtime.store.adopt_legacy(
        LegacyRepresentationAdoption(identifier, "photos", file_id, representation)
    )
    media = Media(
        id=identifier,
        type=MediaType.PHOTO,
        original_filename=original_filename or filename,
        representations=MediaRepresentations(representation),
        associations=associations or (association(),),
        import_source=legacy_import_source("photos", file_id),
    )
    runtime.management.repository.create(
        StoredMedia(media, StoredMediaRepresentations(handle))
    )
    return identifier, original, file_id


def test_canonical_legacy_removal_hides_fallback_and_survives_cleanup(
    management_runtime, media_database
):
    identifier, original, file_id = add_legacy(management_runtime, media_database)
    thumbnail_id = GridFS(media_database, "thumbnails").put(
        original, filename="K.1_240.jpg", contentType="image/jpeg"
    )
    manager = legacy_client(management_runtime, media_database, manager=True)
    reader = legacy_client(management_runtime, media_database)
    assert get(reader, "/fragments/K.1/photo").content == original
    assert get(reader, "/fragments/K.1/thumbnail/small").content == original
    assert (
        manager.simulate_delete(f"/media/{identifier}?fragment=K.1").status_code == 204
    )

    document = {
        "museumNumber": {"prefix": "K", "number": "1", "suffix": ""},
        "hasPhoto": True,
        "thumbnailPath": "/fragments/K.1/thumbnail/small",
    }
    enricher = FragmentMediaEnricher(management_runtime.service)
    for recover in (False, True):
        if recover:
            recover_media(media_database, apply=True, quiescent=True)
        listing = get(reader, "/media?fragment=K.1")
        assert listing.status_code == 200
        assert listing.json == {"media": [], "legacyFallbackAllowed": False}
        detail = enricher.enrich(document, MuseumNumber.of("K.1"))
        row = enricher.enrich_rows([document])[0]
        for summary in (detail, row):
            assert summary["hasPhoto"] is False
            assert "legacyHasPhoto" not in summary
            assert summary["mediaSummary"] == {"count": 0, "types": []}
            assert summary["thumbnailPath"] == document["thumbnailPath"]
        assert get(reader, "/fragments/K.1/photo").status_code == 404
        assert get(reader, "/fragments/K.1/thumbnail/small").status_code == 404
        assert GridFS(media_database, "photos").get(file_id).read() == original
        assert GridFS(media_database, "thumbnails").get(thumbnail_id).read() == original


@pytest.mark.parametrize("claimed_name", ["unrelated.jpg", "K.1.jpg"])
def test_removing_an_unrelated_legacy_filename_preserves_canonical_fallback(
    management_runtime, media_database, claimed_name
):
    identifier, original, _ = add_legacy(
        management_runtime,
        media_database,
        options=LegacyMediaOptions(
            filename="unrelated.jpg", original_filename=claimed_name
        ),
    )
    GridFS(media_database, "photos").put(
        original, filename="K.1.jpg", contentType="image/jpeg"
    )
    manager = legacy_client(management_runtime, media_database, manager=True)
    assert (
        manager.simulate_delete(f"/media/{identifier}?fragment=K.1").status_code == 204
    )
    reader = legacy_client(management_runtime, media_database)
    assert body(get(reader, "/media?fragment=K.1")).get("legacyFallbackAllowed", True)
    assert get(reader, "/fragments/K.1/photo").content == original


def test_removing_an_owned_upload_preserves_legacy_fallback(
    management_runtime, media_database
):
    original = image_bytes("JPEG")
    GridFS(media_database, "photos").put(
        original, filename="K.1.jpg", contentType="image/jpeg"
    )
    manager = legacy_client(management_runtime, media_database, manager=True)
    uploaded = upload(manager)
    assert isinstance(uploaded, testing.Result)
    identifier = body(uploaded)["media"][0]["id"]
    assert (
        manager.simulate_delete(f"/media/{identifier}?fragment=K.1").status_code == 204
    )
    reader = legacy_client(management_runtime, media_database)
    assert body(get(reader, "/media?fragment=K.1")).get("legacyFallbackAllowed", True)
    assert get(reader, "/fragments/K.1/photo").content == original


def test_cross_association_denial_cannot_write_legacy_suppression(
    management_runtime, media_database
):
    identifier, _, _ = add_legacy(
        management_runtime,
        media_database,
        options=LegacyMediaOptions(
            associations=(
                association(fragment_id="K.1"),
                association(fragment_id="K.2"),
            )
        ),
    )
    manager = legacy_client(management_runtime, media_database, manager=True)
    assert (
        manager.simulate_delete(f"/media/{identifier}?fragment=K.1").status_code == 403
    )
    assert media_database.mediaLegacyVisibility.count_documents({}) == 0
    authorized = legacy_client(
        management_runtime, media_database, manager=True, fragment_access=True
    )
    assert (
        authorized.simulate_delete(f"/media/{identifier}?fragment=K.1").status_code
        == 204
    )
    assert not management_runtime.service.legacy_fallback_allowed(
        MuseumNumber.of("K.1")
    )
    assert management_runtime.service.legacy_fallback_allowed(MuseumNumber.of("K.2"))
