from threading import Thread
from wsgiref.simple_server import make_server

import attr
import pytest
import requests
from pymongo.database import Database

import ebl.app
import ebl.tests.media.web.test_legacy_photo_fragment_contract as contract
import ebl.tests.test_app_bootstrap as bootstrap
from ebl.context import Context
from ebl.fragmentarium.application.cropped_sign_image import (
    Base64,
    CroppedSign,
    CroppedSignImage,
)
from ebl.fragmentarium.domain.annotation import (
    Annotation,
    AnnotationData,
    Annotations,
    AnnotationValueType,
    Geometry,
    PcaClustering,
)
from ebl.tests.media.web.test_legacy_photo_fragment_contract import (
    ROUTES,
    SuppressedPhotoCase,
    fragment_document,
)
from ebl.transliteration.domain.museum_number import MuseumNumber

bootstrap_environment = bootstrap.bootstrap_environment
suppressed_photo_case = contract.suppressed_photo_case


def seed_cropped_signs(context: Context) -> str:
    fragment = context.fragment_repository.query_by_museum_number(
        MuseumNumber.of("K.100")
    )
    context.fragment_repository.create(
        attr.evolve(fragment, number=MuseumNumber.of("K.101"))
    )
    for number in (MuseumNumber.of("K.100"), MuseumNumber.of("K.101")):
        image_id = f"review-crop-{number}"
        annotation = Annotation(
            Geometry(0, 0, 10, 10),
            AnnotationData(
                "review-annotation",
                "",
                AnnotationValueType.HAS_SIGN,
                [0, 0, 0],
                "reviewSign",
            ),
            CroppedSign(image_id, "review sign"),
            PcaClustering("review-cluster", 0, "canonical", True, 1, True),
        )
        context.annotations_repository.create_or_update(
            Annotations(number, [annotation])
        )
        context.cropped_sign_images_repository.create_many(
            [CroppedSignImage(image_id, Base64("review-base64"), number)]
        )
    return fragment.script.period.long_name


@pytest.mark.usefixtures("bootstrap_environment")
def test_disabling_media_api_keeps_removed_legacy_photo_hidden_over_http(
    context: Context,
    database: Database,
    suppressed_photo_case: SuppressedPhotoCase,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setenv("MONGODB_DB", database.name)
    monkeypatch.setenv("MEDIA_API_ENABLED", "false")
    monkeypatch.setenv("MEDIA_UPLOAD_ENABLED", "false")
    disabled_context = ebl.app.create_context()
    assert disabled_context.media is None
    application = ebl.app.create_app(
        attr.evolve(disabled_context, auth_backend=context.auth_backend)
    )
    script = seed_cropped_signs(disabled_context)
    case = suppressed_photo_case
    with make_server("127.0.0.1", 0, application) as server:
        thread = Thread(target=server.serve_forever, daemon=True)
        thread.start()
        try:
            origin = f"http://127.0.0.1:{server.server_port}"
            legacy_url = origin + "/fragments/K.100/photo"
            legacy = requests.get(legacy_url, timeout=10)
            assert legacy.status_code == 404
            marker = database["mediaLegacyVisibility"]
            marker_filter = {"_id": "K.100"}
            marker.update_one(marker_filter, {"$set": {"suppressed": False}})
            available = requests.get(legacy_url, timeout=10)
            assert available.status_code == 200
            assert available.content
            assert available.headers["Cache-Control"] == "private, no-store"
            assert available.headers["Vary"] == "Authorization"
            marker.update_one(marker_filter, {"$set": {"suppressed": True}})
            removed_again = requests.get(legacy_url, timeout=10)
            assert removed_again.status_code == 404
            thumbnail = requests.get(
                origin + "/fragments/K.100/thumbnail/small", timeout=10
            )
            assert thumbnail.status_code == 404
            annotations = requests.get(
                origin + "/fragments/K.100/annotations",
                params={"generateAnnotations": "true"},
                timeout=10,
            )
            assert annotations.status_code == 404
            for path in (
                "/signs/reviewSign/images",
                "/signs/reviewSign/images/cluster/review-cluster",
            ):
                response = requests.get(
                    origin + path, params={"script": script}, timeout=10
                )
                assert response.status_code == 200, response.text
                numbers = [row["fragmentNumber"] for row in response.json()]
                assert numbers == ["K.101"]
            for path, collection in ROUTES.items():
                response = requests.get(origin + path, timeout=10)
                assert response.status_code == 200, response.text
                document = fragment_document(response.json(), collection)
                assert document["hasPhoto"] is False
                assert "legacyHasPhoto" not in document
                assert "mediaSummary" not in document
                original = case.before_removal[path]
                thumbnail_key = "thumbnailPath"
                has_thumbnail = thumbnail_key in original
                assert (thumbnail_key in document) == has_thumbnail
                expected_thumbnail = original.get(thumbnail_key)
                assert document.get(thumbnail_key) == expected_thumbnail
            for path in ("/media?fragment=K.100", case.managed_original):
                response = requests.get(origin + path, timeout=10)
                assert response.status_code == 404
        finally:
            server.shutdown()
            thread.join(timeout=10)
        assert not thread.is_alive()
