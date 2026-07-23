import falcon
import pytest

from ebl.tests.factories.fragment import TransliteratedFragmentFactory
from ebl.tests.fragmentarium.conftest import KNOWN_REALIA_ID, OTHER_REALIA_ID

ENTITY_SPAN = {"id": "Entity-1", "type": "PERSONAL_NAME", "span": ["Word-2"]}
REALIA_SPAN = {"id": "Realia-1", "realiaId": KNOWN_REALIA_ID, "span": ["Word-2"]}


@pytest.fixture
def annotation_url(fragmentarium):
    fragment = TransliteratedFragmentFactory.build().set_token_ids()
    fragmentarium.create(fragment)
    return f"/fragments/{fragment.number}/named-entities"


def post(client, url, payload):
    return client.simulate_post(url, json=payload)


@pytest.mark.parametrize(
    "payload,expected",
    [
        pytest.param(
            {"namedEntities": [ENTITY_SPAN, {**ENTITY_SPAN, "id": "Entity-2"}]},
            {"namedEntities": [ENTITY_SPAN], "realia": []},
            id="same_tag_same_span",
        ),
        pytest.param(
            {"realia": [REALIA_SPAN, {**REALIA_SPAN, "id": "Realia-2"}]},
            {"namedEntities": [], "realia": [REALIA_SPAN]},
            id="same_realia_same_span",
        ),
    ],
)
def test_duplicates_are_dropped(
    client, stored_realia, annotation_url, payload, expected
):
    post_result = post(client, annotation_url, payload)

    assert post_result.status == falcon.HTTP_OK
    assert client.simulate_get(annotation_url).json == expected


@pytest.mark.parametrize(
    "payload",
    [
        pytest.param(
            {
                "namedEntities": [
                    ENTITY_SPAN,
                    {**ENTITY_SPAN, "id": "Entity-2", "type": "DIVINE_NAME"},
                ]
            },
            id="different_tags_same_span",
        ),
        pytest.param(
            {
                "namedEntities": [
                    ENTITY_SPAN,
                    {**ENTITY_SPAN, "id": "Entity-2", "span": ["Word-3"]},
                ]
            },
            id="same_tag_different_span",
        ),
        pytest.param(
            {
                "realia": [
                    REALIA_SPAN,
                    {**REALIA_SPAN, "id": "Realia-2", "realiaId": OTHER_REALIA_ID},
                ]
            },
            id="different_realia_same_span",
        ),
        pytest.param(
            {"namedEntities": [ENTITY_SPAN], "realia": [REALIA_SPAN]},
            id="tag_and_realia_same_span",
        ),
    ],
)
def test_distinct_annotations_are_kept(client, stored_realia, annotation_url, payload):
    post_result = post(client, annotation_url, payload)

    assert post_result.status == falcon.HTTP_OK
    result = client.simulate_get(annotation_url).json
    assert result["namedEntities"] == payload.get("namedEntities", [])
    assert result["realia"] == payload.get("realia", [])


def test_conflicting_ids_within_named_entities_are_rejected(
    client, stored_realia, annotation_url
):
    conflicting = {**ENTITY_SPAN, "type": "DIVINE_NAME", "span": ["Word-3"]}

    post_result = post(
        client, annotation_url, {"namedEntities": [ENTITY_SPAN, conflicting]}
    )

    assert post_result.status == falcon.HTTP_UNPROCESSABLE_ENTITY
    assert "Entity-1" in post_result.json["description"]


def test_id_reused_across_kinds_is_rejected(client, stored_realia, annotation_url):
    payload = {
        "namedEntities": [ENTITY_SPAN],
        "realia": [{**REALIA_SPAN, "id": "Entity-1"}],
    }

    post_result = post(client, annotation_url, payload)

    assert post_result.status == falcon.HTTP_UNPROCESSABLE_ENTITY
    assert "Entity-1" in post_result.json["description"]


def test_conflicting_ids_write_nothing(client, stored_realia, annotation_url):
    conflicting = {**ENTITY_SPAN, "type": "DIVINE_NAME", "span": ["Word-3"]}

    post(client, annotation_url, {"namedEntities": [ENTITY_SPAN, conflicting]})

    assert client.simulate_get(annotation_url).json == {
        "namedEntities": [],
        "realia": [],
    }
