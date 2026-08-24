from typing import Any, Dict

import pytest

from ebl.iiif.application.iiif_schemas import ManifestSchema
from ebl.iiif.application.manifest_builder import ManifestBuilder, ManifestProvider
from ebl.iiif.application.manifest_sources import MetadataSource
from ebl.iiif.domain.manifest import PRESENTATION_CONTEXT
from ebl.tests.iiif.factories import (
    BASE_URL,
    MEDIA_ID,
    RIGHTS,
    MissingImageService,
    StubImageService,
    fragment_source,
    identifiers,
    media_source,
    rendering_source,
)


def dump(fragment, image_services=None) -> Dict[str, Any]:
    builder = ManifestBuilder(
        identifiers(),
        image_services or MissingImageService(),
        ManifestProvider("https://www.example.org/", "eBL"),
    )
    dumped = ManifestSchema().dump(builder.build(fragment))
    assert isinstance(dumped, dict)
    return dumped


@pytest.fixture
def manifest_json():
    return dump(
        fragment_source(
            metadata=[MetadataSource("Script", "Neo-Assyrian")],
            summary="A fragment.",
            homepage_url="https://www.example.org/fragmentarium/K.1",
            record_url=f"{BASE_URL}/fragments/K.1",
        )
    )


def test_the_presentation_context_is_emitted(manifest_json):
    assert manifest_json["@context"] == PRESENTATION_CONTEXT


def test_identifiers_are_absolute_http_uris(manifest_json):
    canvas = manifest_json["items"][0]

    assert manifest_json["id"].startswith("https://")
    assert canvas["id"].startswith("https://")
    assert canvas["items"][0]["id"].startswith("https://")


def test_required_manifest_properties_are_present(manifest_json):
    for key in ["id", "type", "label", "items"]:
        assert key in manifest_json

    assert manifest_json["type"] == "Manifest"
    assert manifest_json["items"]


def test_language_map_values_are_arrays_of_strings(manifest_json):
    assert manifest_json["label"] == {"none": ["K.1"]}
    assert manifest_json["summary"] == {"en": ["A fragment."]}
    assert manifest_json["metadata"][0]["label"] == {"en": ["Script"]}


def test_camel_case_keys_are_used(manifest_json):
    assert "requiredStatement" in manifest_json
    assert "seeAlso" in manifest_json
    assert "viewingDirection" in manifest_json
    assert "required_statement" not in manifest_json
    assert "see_also" not in manifest_json


def test_canvas_carries_both_dimensions(manifest_json):
    canvas = manifest_json["items"][0]

    assert canvas["width"] == 4000
    assert canvas["height"] == 3000
    assert canvas["type"] == "Canvas"


def test_the_painting_annotation_is_fully_serialized(manifest_json):
    page = manifest_json["items"][0]["items"][0]
    annotation = page["items"][0]

    assert page["type"] == "AnnotationPage"
    assert annotation["type"] == "Annotation"
    assert annotation["motivation"] == "painting"
    assert annotation["target"] == manifest_json["items"][0]["id"]
    assert annotation["body"]["type"] == "Image"


def test_rights_and_provider_are_serialized(manifest_json):
    assert manifest_json["rights"] == RIGHTS
    assert manifest_json["provider"][0]["type"] == "Agent"


def test_absent_optional_properties_are_omitted_not_null():
    manifest_json = dump(fragment_source())

    for key in ["summary", "homepage", "seeAlso", "metadata", "partOf"]:
        assert key not in manifest_json


def test_no_service_key_when_no_image_service_exists():
    manifest_json = dump(fragment_source())
    body = manifest_json["items"][0]["items"][0]["items"][0]["body"]

    assert "service" not in body


def test_the_image_service_is_serialized_when_present():
    manifest_json = dump(fragment_source(), StubImageService())
    body = manifest_json["items"][0]["items"][0]["items"][0]["body"]

    assert body["service"] == [
        {
            "id": f"{BASE_URL}/iiif/3/image/{MEDIA_ID}",
            "type": "ImageService3",
            "profile": "level2",
        }
    ]


def test_rendering_is_serialized_without_inlining_content():
    manifest_json = dump(
        fragment_source(media=[media_source(rendering=rendering_source())])
    )
    rendering = manifest_json["items"][0]["rendering"][0]

    assert rendering["id"] == f"{BASE_URL}/copy.svg"
    assert rendering["format"] == "image/svg+xml"
    assert set(rendering) == {"id", "type", "label", "format"}


def test_a_canvas_label_is_omitted_when_absent():
    manifest_json = dump(fragment_source(media=[media_source(label=None)]))

    assert "label" not in manifest_json["items"][0]


def test_zero_is_not_treated_as_an_empty_value():
    assert dump(fragment_source())["items"][0]["width"] == 4000
